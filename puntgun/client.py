import functools
from typing import List

import tweepy
from loguru import logger

from conf.encrypto import load_or_generate_private_key
from conf.secret import load_or_request_all_secrets
from recorder import Recorder, Recordable, Record
from rules.user import User


class TwitterClientError(Exception):
    """Class for wrapping all Twitter client library custom errors."""

    def __init__(self):
        super().__init__(f'Twitter client raises unrecoverable error while querying Twitter API')


class TwitterApiError(Exception):
    """Corresponding to one https://developer.twitter.com/en/support/twitter-api/error-troubleshooting#partial-errors"""
    title = 'generic twitter api error'

    def __init__(self, title, ref_url, detail, parameter, value):
        super().__init__(f'{detail} Refer: {ref_url}')
        self.title = title
        self.ref_url = ref_url
        self.detail = detail
        self.parameter = parameter
        self.value = value

    @staticmethod
    def from_response(resp_error: dict):
        # build an accurate error type according to the response content
        for subclass in TwitterApiError.__subclasses__():
            if subclass.title == resp_error.get('title'):
                return subclass(
                    title=resp_error.get('title', ''),
                    # when parsing from Twitter API response, key is 'type'
                    # when parsing from :class:`Record` instance, key is 'ref_url'
                    ref_url=resp_error.get('type', resp_error.get('ref_url', '')),
                    detail=resp_error.get('detail', ''),
                    parameter=resp_error.get('parameter', ''),
                    value=resp_error.get('value', ''))

        # if we haven't written a subclass for given error, return generic error
        return TwitterApiError(
            title=resp_error.get('title', ''),
            ref_url=resp_error.get('type', resp_error.get('ref_url', '')),
            detail=resp_error.get('detail', ''),
            parameter=resp_error.get('parameter', ''),
            value=resp_error.get('value', ''))


class ResourceNotFoundError(TwitterApiError):
    """
    For example, if you try to query information about a not-exist user id,
    this error will be returned by Twitter server and raised by the tool.
    """
    title = 'Not Found Error'


class TwitterApiErrors(Exception, Recordable):
    """
    This error raised when a Twitter Dev API query returns http status code 200,
    but has an "errors" field in the response body,
    which indicates several "Partial error" occurs
    and the result only contains what Twitter server can figured out.

    https://developer.twitter.com/en/support/twitter-api/error-troubleshooting#partial-errors

    Corresponding to errors returned with one API query's response,
    contains a list of :class:`TwitterApiError`.
    """

    def __init__(self, query_func_name: str, query_params, resp_errors: List[dict]):
        """Details for debugging via log."""
        self.query_func_name = query_func_name
        self.query_params = query_params
        self.errors = [TwitterApiError.from_response(e) for e in resp_errors]

        msg = f"Twitter Server returned partial errors when querying API: " \
              f"function called: [{query_func_name}], " \
              f"params: [{query_params}], " \
              f"errors: [{self.errors}]"

        logger.info(msg)
        super().__init__(msg)

    def __bool__(self):
        return bool(self.errors)

    def __len__(self):
        return len(self.errors)

    def __iter__(self):
        return iter(self.errors)

    def __getitem__(self, index):
        return self.errors[index]

    def to_record(self):
        return Record(type='twitter_api_errors',
                      data={'query_func_name': self.query_func_name,
                            'query_params': self.query_params,
                            'errors': [e.__dict__ for e in self.errors]})

    @staticmethod
    def parse_from_record(record: Record):
        data = record.data
        return TwitterApiErrors(data.get('query_func_name', ''),
                                data.get('query_params', ()),
                                data.get('errors', []))


def record_twitter_api_errors(client_func):
    """
    Decorator for recording Twitter API errors returned by tweepy or Twitter server
    while invoking :class:`tweepy.Client`.
    """

    def record_api_errors(request_params, resp_errors):
        Recorder.record(TwitterApiErrors(str(client_func), request_params, resp_errors))

    def decorator(*args, **kwargs):
        try:
            resp = client_func(*args, **kwargs)
            if hasattr(resp, 'errors'):
                record_api_errors(kwargs, resp.errors)
            return resp
        except tweepy.errors.TweepyException as e:
            # We have no idea how to handle the error tweepy throws out.
            # just wrap it in a custom exception and let it fails the entire process.
            logger.exception('Client raises unrecoverable error while querying Twitter API')
            raise TwitterClientError from e

    return decorator


class Client(object):
    """
    Adapter of :class:`tweepy.Client` for handling requests and responses to the Twitter API.

    Due to the rate limit set by the Twitter API,
    and tweepy will actively sleep and wait for the next attempt when hit the limit,
    the methods in this class are blocking.

    So here is the solution:
      1. One invocation on methods will send only **one** request to the Twitter API, makes the invocation "atomic".
      2. This class doesn't care about the terrible blocking, let the caller handle it.

    Ref:
      * https://developer.twitter.com/en/docs/twitter-api/rate-limits
      * It's so sweet that tweepy has inner retry logic for resumable 429 Too Many Request status code.
        https://github.com/tweepy/tweepy/blob/master/tweepy/client.py#L102-L114
    """

    # additional url params for querying Twitter user state api,
    # for letting the API know which fields we want to get.
    __user_api_params = {'user_auth': True,
                         'user_fields': ['id', 'name', 'username', 'pinned_tweet_id', 'profile_image_url',
                                         'created_at', 'description', 'public_metrics', 'protected', 'verified'],
                         'expansions': 'pinned_tweet_id',
                         'tweet_fields': ['text']}

    def __init__(self, tweepy_client: tweepy.Client):
        # Add a decorator to record Twitter API errors in response on every call to the tweepy client.
        # can't call '__name__' on mocked functions (MagicMock) even use mock.configure_mock(__name__='...')
        # so manually set the function names rather than using fn.__name__
        for name, fn in [('get_users', tweepy_client.get_users), ('block', tweepy_client.block)]:
            setattr(tweepy_client, name, record_twitter_api_errors(fn))

        self.clt = tweepy_client
        # tweepy 4.10.0 changed return structure of tweepy.Client.get_me()
        # it's different from tweepy.Client.get_user()'s return structure
        # it's not the "data: [my_data]", but "data: my_data"
        self.me = User.from_response(self.clt.get_me().data, '')
        self.id = self.me.id
        self.name = self.me.name

    @staticmethod
    @functools.lru_cache(maxsize=1)
    def singleton():
        secrets = load_or_request_all_secrets(load_or_generate_private_key())
        return Client(tweepy.Client(consumer_key=secrets['ak'],
                                    consumer_secret=secrets['aks'],
                                    access_token=secrets['at'],
                                    access_token_secret=secrets['ats']))

    def get_users_by_usernames(self, names: List[str]):
        """
        Calling :meth:`tweepy.Client.get_users`.
        **rate limit: 900 / 15 min**
        https://developer.twitter.com/en/docs/twitter-api/users/lookup/api-reference/get-users-by
        """
        if len(names) > 100:
            raise ValueError('at most 100 usernames per request')

        return self._user_resp_to_user_instances(self.clt.get_users(usernames=names, **self.__user_api_params))

    def get_users_by_ids(self, ids: List[int | str]):
        """
        Calling :meth:`tweepy.Client.get_users`.
        **rate limit: 900 / 15 min**
        https://developer.twitter.com/en/docs/twitter-api/users/lookup/api-reference/get-users
        """
        if len(ids) > 100:
            raise ValueError('at most 100 user ids per request')

        return self._user_resp_to_user_instances(self.clt.get_users(ids=ids, **self.__user_api_params))

    @staticmethod
    def _user_resp_to_user_instances(resp: tweepy.Response):
        """Build a list of :class:`User` instances from one response."""
        if not resp.data:
            return []

        pinned_tweets = resp.includes.get('tweets', [])

        def resp_to_user(data: dict) -> User:
            """Build one user instance"""

            # find this user's pinned tweet
            # Twitter's response doesn't guarantee the order of pinned tweets,
            # because there are users who don't have pinned tweets:
            # resp.data: [u1(has), u2(hasn't), u3(has)]
            # resp.includes.tweets: [u1_pinned_tweet, u3_pinned_tweet]
            pinned_tweet = [t for t in pinned_tweets if t['id'] == data['pinned_tweet_id']]
            pinned_tweet_text = pinned_tweet[0]['text'] if pinned_tweet else ''
            return User.from_response(data, pinned_tweet_text)

        return [resp_to_user(d) for d in resp.data]

    def block_user_by_id(self, target_user_id: int | str) -> bool:
        """
        Calling :meth:`tweepy.Client.block`.
        The rate limit is pretty slow, and somehow I think this is the bottleneck of whole pipeline
        if you don't use complex rules.
        Sadly, the former block list CSV import method is no longer available.
        **rate limit: 50 / 15 min**
        https://help.twitter.com/en/using-twitter/advanced-twitter-block-options
        https://developer.twitter.com/en/docs/twitter-api/users/blocks/api-reference/post-users-user_id-blocking
        """

        return self.clt.block(target_user_id=target_user_id).data['blocking']


class NeedClient(object):
    """
    Some rules need a :class:`Client` to call for getting extra information.
    This class provides a lazy loading client field (call Client.singleton()).

    This class can also be used to label filter rules that take time to run their judgements
    (because they need to query Twitter API) and can't return immediately.
    """

    @property
    def client(self) -> Client:
        """
        Lazy load the client field to avoid:
        run unit test -> initialize this class -> call Client.singleton() -> require terminal input -> test fail
        https://github.com/samuelcolvin/pydantic/issues/1035#issuecomment-559043877

        Directly return the invocation for now, may complicate it for load balancing in the future.
        """
        return Client.singleton()
