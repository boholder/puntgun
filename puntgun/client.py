import functools

import tweepy
from loguru import logger

from conf.encrypto import load_or_generate_private_key
from conf.secret import load_or_request_all_secrets
from recorder import Recorder, Recordable
from user import User

"""Various specific errors for this project."""
from typing import List, Callable, Any


class TwitterClientError(Exception):
    """Class for wrapping all Twitter client library custom errors."""


class TwitterApiErrors(Exception, Recordable):
    """
    This error raised when a Twitter Dev API query returns http status code 200,
    but has an "errors" field in the response body,
    which indicates several "Partial error" occurs
    and the result only contains what Twitter server can figured out.

    https://developer.twitter.com/en/support/twitter-api/error-troubleshooting#partial-errors

    Corresponding to one API query's response,
    contains a list of :class:`puntgun.client.TwitterApiError`.
    """

    def __init__(self, query_func_name: str, query_params, resp_errors: List[dict]):
        """Details for debugging via log."""
        self.query_func_name = query_func_name
        self.query_params = query_params
        self.errors = [TwitterApiError.from_response(e) for e in resp_errors]
        super().__init__(f"Twitter Server returned partial errors when querying API:"
                         f" function called: {query_func_name}, params: {query_params}, errors: {self.errors}")

    def __bool__(self):
        return bool(self.errors)

    def __len__(self):
        return len(self.errors)

    def __iter__(self):
        return iter(self.errors)

    def __getitem__(self, index):
        return self.errors[index]

    def record(self) -> str:
        """TODO"""
        pass


class TwitterApiError(Exception):
    title = 'generic twitter api error'

    def __init__(self, title, ref_url, detail, parameter, value):
        super().__init__(f'{detail} Refer: {ref_url}.')
        self.title = title
        self.ref_url = ref_url
        self.detail = detail
        self.parameter = parameter
        self.value = value

    @staticmethod
    def from_response(resp_error: dict):
        # build an accurate error type according to the response content
        for subclass in TwitterApiError.__subclasses__():
            if subclass.title == resp_error['title']:
                return subclass(
                    title=resp_error['title'],
                    ref_url=resp_error['type'],
                    detail=resp_error['detail'],
                    parameter=resp_error['parameter'],
                    value=resp_error['value'])

        # if we haven't written a subclass for given error, return generic error
        return TwitterApiError(
            title=resp_error['title'],
            ref_url=resp_error['type'],
            detail=resp_error['detail'],
            parameter=resp_error['parameter'],
            value=resp_error['value'])


class ResourceNotFoundError(TwitterApiError):
    """
    For example, if you try to query information about a not-exist user id,
    this error will be returned by Twitter server and raised by the tool.
    """
    title = 'Not Found Error'


def record_errors(tweepy_invoking: Callable[[Any], tweepy.Response]):
    """
    Decorator for recording Twitter API errors returned by tweepy or Twitter server
    while invoking :class:`tweepy.Client`.
    """

    def record_api_errors(request_params, resp_errors):
        Recorder.record(TwitterApiErrors(tweepy_invoking.__name__, request_params, resp_errors))

    def decorator(*args, **kwargs):
        try:
            resp = tweepy_invoking(*args, **kwargs)
            if hasattr(resp, "errors"):
                record_api_errors(kwargs, resp.errors)
            return resp
        except tweepy.errors.TweepyException as e:
            # We have no idea how to handle the error tweepy throws out.
            # just wrap it in a custom exception and let it fails the entire process.
            logger.error('Client throws unrecoverable error while querying Twitter API', e)
            raise TwitterClientError from e

    return decorator


class Client(object):
    """ Adapter of :class:`tweepy.Client` for handling requests and responses to the Twitter API. """

    # additional url params for querying Twitter user state api
    __user_api_params = {'user_auth': True,
                         'user_fields': ['id', 'name', 'username', 'pinned_tweet_id', 'profile_image_url',
                                         'created_at', 'description', 'public_metrics', 'protected', 'verified'],
                         'expansions': 'pinned_tweet_id',
                         'tweet_fields': ['text']}

    def __init__(self, tweepy_client: tweepy.Client):
        self.clt = tweepy_client
        # tweepy 4.10.0 changed return structure of tweepy.Client.get_me()
        self.me = User.from_response(self.clt.get_me()['data'], '')
        self.id = self.me.id
        self.name = self.me.name
        logger.info(f'The client initialized as Twitter user: {self.name}')

    @staticmethod
    @functools.lru_cache(maxsize=1)
    def singleton():
        secrets = load_or_request_all_secrets(load_or_generate_private_key())
        return Client(tweepy.Client(consumer_key=secrets['ak'],
                                    consumer_secret=secrets['aks'],
                                    access_token=secrets['at'],
                                    access_token_secret=secrets['ats']))

    def get_users_by_usernames(self, names: List[str]):
        """https://developer.twitter.com/en/docs/twitter-api/users/lookup/api-reference/get-users-by"""

        @record_errors
        def get_users(**kwargs):
            return self.clt.get_users(**kwargs)

        def one_query(n):
            return self.__user_resp_to_user_instances(get_users(usernames=n, **self.__user_api_params))

        result_list = [one_query(g) for g in self.__split_to_one_hundred(names)]
        # flatten it
        return [u for sub in result_list for u in sub]

    @staticmethod
    def __user_resp_to_user_instances(resp: tweepy.Response):
        if not resp.data:
            return []

        pinned_tweets = resp.includes['tweets'] if 'tweets' in resp.includes else []

        def resp_to_user(data: dict) -> User:
            # find this user's pinned tweet
            # Twitter's response doesn't guarantee the order of pinned tweets,
            # because there are users who don't have pinned tweets:
            # resp.data: [u1(has), u2(hasn't), u3(has)]
            # resp.includes.tweets: [u1_pinned_tweet, u3_pinned_tweet]
            pinned_tweet = [t for t in pinned_tweets if t['id'] == data['pinned_tweet_id']]
            pinned_tweet_text = pinned_tweet[0]['text'] if pinned_tweet else ''
            return User.from_response(data, pinned_tweet_text)

        return [resp_to_user(d) for d in resp.data]

    @staticmethod
    def __split_to_one_hundred(lst: list):
        """Some Twitter API limits the number of usernames in a single request to 100."""
        for i in range(0, len(lst), 100):
            yield lst[i:i + 100]
