import functools
import os
from typing import List, Callable, Any, Tuple, Union, TypeVar

import reactivex as rx
import tweepy
from reactivex import operators as op
from tweepy import Client, OAuth1UserHandler

import util
from old.test.client.hunter import Hunter, MixedResultProcessingWrapper
from model.errors import TwitterApiErrors, TwitterClientError
from rules.user import User

NO_VALUE_PROVIDED = 'No value provided.'

# keys for getting twitter auth api secrets from environment variables
API_KEY = 'TWI_API_KEY'
API_KEY_SECRET = 'TWI_API_KEY_SECRET'
ACCESS_TOKEN = 'TWI_ACCESS_TOKEN'
ACCESS_TOKEN_SECRET = 'TWI_ACCESS_TOKEN_SECRET'


class TweepyHunter(Hunter):
    """
    Reactive proxy wrapper of "tweepy" library,
    use reactive streams and custom data types to transform data.

    Initializing instance via interact with user through console,
    it requires user to provide secrets like Twitter API key and secret, etc.
    """
    logger = util.get_logger(__qualname__)

    # additional url params for querying Twitter user state api
    user_api_params = {'user_auth': True,
                       'user_fields': ['id', 'name', 'username', 'pinned_tweet_id', 'profile_image_url',
                                       'created_at', 'description', 'public_metrics', 'protected', 'verified'],
                       'expansions': 'pinned_tweet_id',
                       'tweet_fields': ['text']}

    @staticmethod
    @functools.lru_cache(maxsize=1)
    def singleton() -> 'TweepyHunter':
        """Get singleton instance of Hunter"""
        return TweepyHunter(init_tweepy_client())

    def __init__(self, client: tweepy.Client):
        """You should only get instance of this class via ``instance`` static method."""
        self.client = client

        self.me = User.from_response(self.client.get_me().data[0], '')
        self.id = self.me.id
        self.name = self.me.name

        self.logger.info('[{}] the hunter dressed up.\n'.format(self.name))

    def observe(self,
                user_id: int = None,
                username: str = None,
                user_ids: List[int] = None,
                usernames: List[str] = None) \
            -> MixedResultProcessingWrapper:
        """Query user information."""

        def transform(resp: tweepy.Response) -> User:
            data = resp.data[0]
            pinned_tweet_id = data['pinned_tweet_id']
            # every user can have at most one pinned tweet,
            # don't know why Twitter API returns a list type
            # if one user doesn't have pinned tweet, the "includes" field isn't have "tweets" field
            pinned_tweet_text: str = [t['text'] for t in resp.includes['tweets']][0] if pinned_tweet_id else ''

            return User.from_response(data, pinned_tweet_text)

        def multi_transform(resp: tweepy.Response) -> List[User]:
            def data_to_user(_data: dict) -> User:
                # find this user's pinned tweet
                pinned_tweet = [t for t in pinned_tweets if t['id'] == _data['pinned_tweet_id']]
                pinned_tweet_text = pinned_tweet[0]['text'] if pinned_tweet else ''

                return User.from_response(_data, pinned_tweet_text)

            pinned_tweets = resp.includes['tweets'] if 'tweets' in resp.includes else []

            return [data_to_user(d) for d in resp.data]

        if user_id:
            return query_then_transform(rx.of(user_id), self.get_user_by_id, transform)
        elif username:
            return query_then_transform(rx.of(username), self.get_user_by_name, transform)
        elif user_ids:
            # API allows querying up to 100 users at once, so we need to split the list into 100 size chunks
            return query_then_transform(rx.from_iterable(user_ids).pipe(op.buffer_with_count(100)),
                                        self.get_users_by_id, multi_transform)
        elif usernames:
            return query_then_transform(rx.from_iterable(usernames).pipe(op.buffer_with_count(100)),
                                        self.get_users_by_name, multi_transform)
        else:
            raise ValueError(NO_VALUE_PROVIDED)

    def get_user_by_id(self, uid: int) -> tweepy.Response:
        return self.client.get_user(user_id=uid, **self.user_api_params)

    def get_user_by_name(self, name: str) -> tweepy.Response:
        return self.client.get_user(username=name, **self.user_api_params)

    def get_users_by_id(self, ids: List[int]) -> tweepy.Response:
        return self.client.get_users(ids=ids, **self.user_api_params)

    def get_users_by_name(self, names) -> tweepy.Response:
        return self.client.get_users(usernames=names, **self.user_api_params)


T = TypeVar('T')
R = TypeVar('R')


def query_then_transform(source: rx.Observable[T],
                         query_func: Callable[[T], tweepy.Response],
                         transform_func: Callable[[tweepy.Response], Any]) \
        -> MixedResultProcessingWrapper:
    """
    Query Twitter Dev API and transform response into two observables.

    :param source: observable source of data to query
    :param query_func: function to query data using Twitter API
    :param transform_func: function to transform data from Twitter API response,
            one response can be transformed into multiple data
    :return: two observables of transformed data and errors
    """
    return MixedResultProcessingWrapper(source.pipe(query_api_operator(query_func, transform_func)))


def query_api_operator(query_func: Callable[[T], tweepy.Response],
                       transform_func: Callable[[tweepy.Response], Union[R, List[R]]]):
    """
    A custom rx operator that:

    1. query Twitter Dev API (calling query_func({element_of_stream})).
    2. handle the response via http status code (return? retry? signal error?)
    3. transform the response to custom data types (calling transform_func).
    """

    def _query_api(source):
        def subscribe(observer, scheduler=None):
            def on_next(value):
                try:
                    make_query_and_add_result_into_stream(observer, value)
                except tweepy.errors.TweepyException as e:
                    # For now, we have no idea how to handle the error tweepy throws out.
                    # just wrap it in a custom exception and let it fails the stream.
                    TweepyHunter.logger.error('Client throws error when querying Twitter API', e)
                    observer.on_error(TwitterClientError(e))

            return source.subscribe(
                on_next=on_next,
                on_error=observer.on_error,
                on_completed=observer.on_completed,
                scheduler=scheduler)

        return rx.create(subscribe)

    def make_query_and_add_result_into_stream(observer, query_value):
        models, errors = one_query(query_value)

        # add errors and valid results to the stream
        # the returned observable is mixed with errors and results
        # one query may result in a list of valid results
        if isinstance(models, list):
            [observer.on_next(v) for v in models if v]
        elif models:
            observer.on_next(models)

        if errors:
            [observer.on_next(e) for e in errors.errors]

    @util.log_error_with(TweepyHunter.logger)
    def one_query(element) -> Tuple[Any, TwitterApiErrors]:
        # It's so sweet that tweepy has inner retry logic for
        # resumable 429 Too Many Request status code.
        # https://github.com/tweepy/tweepy/blob/master/tweepy/client.py#L102-L114
        response = query_func(element)

        # There may be no such user exist corresponding to the given id or username
        # in this case, the response.data = None
        # (write custom data types' __bool__ method to handle this case)
        #
        # What's more, one query can be partly succeed,
        # so one query may result in two type of elements: valid results and api errors
        # https://developer.twitter.com/en/support/twitter-api/error-troubleshooting#partial-errors
        models = transform_func(response) if response.data else None
        errors = TwitterApiErrors(response.errors) if response.errors else None
        return models, errors

    return _query_api


def init_tweepy_client() -> tweepy.Client:
    """Initiating the tweepy client by interacting with user via terminal,
    asking for Twitter API secrets."""

    def save_secrets_to_env(_api_key, _api_secret, _access_token, _access_token_secret):
        os.environ[API_KEY] = _api_key
        os.environ[API_KEY_SECRET] = _api_secret
        os.environ[ACCESS_TOKEN] = _access_token
        os.environ[ACCESS_TOKEN_SECRET] = _access_token_secret

    def get_access_token_and_secret(_api_key, _api_secret):
        _access_token, _access_token_secret = get_access_token_pair_from_env()
        if _access_token and _access_token_secret:
            print('Got the access token and secret from environment variables.')
            return _access_token, _access_token_secret
        else:
            return get_access_token_pair_via_authorization_pin(_api_key, _api_secret)

    def get_access_token_pair_via_authorization_pin(_api_key, _api_secret):
        oauth1_user_handler = OAuth1UserHandler(_api_key, _api_secret, callback='oob')

        print('Now you need to authorize your app to access your Twitter account\n'
              'by entering the PIN code you get from newly opened browser window:\n'
              + oauth1_user_handler.get_authorization_url() + '\n')

        pin = util.get_input_from_terminal('PIN')
        return oauth1_user_handler.get_access_token(pin)

    def get_access_token_pair_from_env():
        return os.environ.get(ACCESS_TOKEN), os.environ.get(ACCESS_TOKEN_SECRET)

    def get_consumer_key_and_secret():
        _api_key, _api_secret = get_consumer_key_pair_from_env()
        if _api_key and _api_secret:
            print('Got the Dev API key and secret from environment variables.')
            return _api_key, _api_secret
        else:
            return get_consumer_key_pair_from_input()

    def get_consumer_key_pair_from_env():
        return os.environ.get(API_KEY), os.environ.get(API_KEY_SECRET)

    def get_consumer_key_pair_from_input():
        print('We need a "Twitter Dev OAuth App API" to start.\n'
              'You can get one by signing up on [ https://developer.twitter.com/en ] for free,\n'
              'but first you need to bind a phone number with your Twitter account.\n'
              '(Can unbind the phone after signed up Dev API)\n\n'
              'And don\'t forget to turn on OAuth 1.0a in your App settings:\n'
              '  1. Set the App permissions to "Read and write".\n'
              '  2. Set the callback, website URL to "https://twitter.com" for passing setting check.\n\n'
              'We\'ll use the pin based auth method, so we don\'t really need to deploy a server for callback.\n'
              '-> https://developer.twitter.com/en/docs/authentication/oauth-1-0a/pin-based-oauth\n\n')

        return util.get_input_from_terminal('Api key'), util.get_input_from_terminal('Api secret')

    # consumer key and secret represents the Twitter's authorization about calling its API
    api_key, api_secret = get_consumer_key_and_secret()
    # access token pair to represent the user's authorization about operating the account
    access_token, access_token_secret = get_access_token_and_secret(api_key, api_secret)

    # It's ok (secure) to save them into env, documentation isn't mention that,
    # but it looks like (and base on my manually test)
    # changing `os.environ` inside python won't affect the host's env.
    # So these value would disappear after python program quit.
    # https://docs.python.org/2/library/os.html#os.environ
    #
    # We can use them somewhere else.
    save_secrets_to_env(api_key, api_secret, access_token, access_token_secret)

    return Client(consumer_key=api_key,
                  consumer_secret=api_secret,
                  access_token=access_token,
                  access_token_secret=access_token_secret)
