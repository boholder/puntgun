import functools
import os
from typing import List, Callable, Any, Tuple

import reactivex as rx
import tweepy
from reactivex import operators as op
from tweepy import Client, OAuth1UserHandler

from puntgun import util
from puntgun.model.errors import TwitterApiErrors, TwitterClientError
from puntgun.model.user import User
from puntgun.spi.twitter_client.hunter import Hunter

NO_VALUE_PROVIDED = 'No value provided.'

# keys for accessing twitter auth api secrets
API_KEY = 'TWI_API_KEY'
API_KEY_SECRET = 'TWI_API_KEY_SECRET'
ACCESS_TOKEN = 'TWI_ACCESS_TOKEN'
ACCESS_TOKEN_SECRET = 'TWI_ACCESS_TOKEN_SECRET'

# additional url params for querying Twitter user state api
USER_PARAM_USER_FIELDS = ['id', 'name', 'username', 'pinned_tweet_id', 'profile_image_url',  # metadata
                          'created_at', 'description', 'public_metrics', 'protected', 'verified']  # metrics
USER_PARAM_EXPANSIONS = 'pinned_tweet_id'
USER_PARAM_TWITTER_FIELDS = ['text']  # metrics


class TweepyHunter(Hunter):
    """
    Reactive wrapper of "tweepy" library,
    use reactive streams and custom data types to transform data.

    Initializing instance via interact with user through console,
    it requires user to provide secrets like Twitter API key and secret, etc.
    """
    logger = util.get_logger(__qualname__)

    @staticmethod
    @functools.lru_cache(maxsize=1)
    def singleton() -> 'TweepyHunter':
        """Get singleton instance of Hunter"""
        return TweepyHunter()

    def __init__(self):
        """You should only get instance of this class via ``instance`` static method."""
        self.client = init_tweepy_client()

        me = self.client.get_me().data
        self.id = me.get('id')
        self.username = me.get('name')

        self.logger.info('[{}] the hunter dressed up.\n'.format(self.username))

    def observe(self,
                user_id: rx.Observable[str] = None,
                username: rx.Observable[str] = None,
                user_ids: rx.Observable[str] = None) \
            -> Tuple[rx.Observable[User, TwitterClientError], rx.Observable[TwitterApiErrors]]:
        """Given user_id, username or a list of user_id,
        get user(s) information via Twitter Dev API.

        :param user_id: stream of single user id
        :param username: stream of username
        :param user_ids: stream of list of user id,
            one list contains up to 100.
            Twitter has an API let us query up to 100 users at once,
            using user id.

        :return: two streams:
            1. a stream of user(s) information, may be stopped by client error.
            2. a stream of Twitter API errors, tells which user(s) information failed to get.
        """

        def get_user_by_id(uid) -> tweepy.Response:
            return self.client.get_user(user_auth=True,
                                        user_fields=USER_PARAM_USER_FIELDS,
                                        expansions=USER_PARAM_EXPANSIONS,
                                        tweet_fields=USER_PARAM_TWITTER_FIELDS,
                                        user_id=uid)

        def get_user_by_username(uname) -> tweepy.Response:
            return self.client.get_user(user_auth=True,
                                        user_fields=USER_PARAM_USER_FIELDS,
                                        expansions=USER_PARAM_EXPANSIONS,
                                        tweet_fields=USER_PARAM_TWITTER_FIELDS,
                                        username=uname)

        def get_users_by_id(**params) -> tweepy.Response:
            return self.client.get_users(user_auth=True,
                                         user_fields=USER_PARAM_USER_FIELDS,
                                         expansions=USER_PARAM_EXPANSIONS,
                                         tweet_fields=USER_PARAM_TWITTER_FIELDS,
                                         **params)

        def transform(resp: tweepy.Response) -> User:
            return User.build_from_response(resp.data, resp.includes['tweets'])

        def multi_transform(resp: tweepy.Response) -> List[User]:
            result = []
            for i in range(len(resp.data)):
                result.append(User.build_from_response(resp.data[i], [resp.includes['tweets'][i]]))
            return result

        if user_id:
            return user_id.pipe(query_and_transform(get_user_by_id, transform))
        elif username:
            return username.pipe(query_and_transform(get_user_by_username, transform))
        elif user_ids:
            return user_ids.pipe(op.buffer_with_count(100),
                                 query_and_transform(get_users_by_id, multi_transform))
        else:
            raise ValueError(NO_VALUE_PROVIDED)


def query_and_transform(query_func: Callable[[Any], tweepy.Response],
                        transform_func: Callable[[tweepy.Response], Any]):
    """
    A custom rx operator that:
    1. query Twitter Dev API (calling query_func({element_of_stream})).
    2. handle the response via http status code (return? retry? signal error?)
    3. if decide to return the response,
        transform the response to custom data types (calling transform_func).
    """

    @util.log_error_with(TweepyHunter.logger)
    def query(element) -> Tuple[Any, TwitterApiErrors]:
        # It's so sweet that tweepy has inner retry logic for
        # resumable 429 Too Many Request status code.
        # https://github.com/tweepy/tweepy/blob/master/tweepy/client.py#L102-L114
        response = query_func(element)

        # One query can be partly succeed,
        # so one query may result in two ongoing elements.
        # https://developer.twitter.com/en/support/twitter-api/error-troubleshooting#partial-errors
        return transform_func(response), TwitterApiErrors(response.errors)

    def _query_and_transform(source):
        def subscribe(observer, scheduler=None):
            def on_next(value):
                try:
                    result, errors = query(value)

                    if isinstance(result, list):
                        [observer.on_next(v) for v in result]
                    else:
                        observer.on_next(result)

                    if errors:
                        observer.on_next(errors)
                except tweepy.errors.TweepyException as e:
                    # for now, we have no idea how to handle the error tweepy throws out.
                    # just wrap it in a custom exception and let it fails the stream.
                    observer.on_error(TwitterClientError(e))

            return source.subscribe(
                on_next=on_next,
                on_error=observer.on_error,
                on_completed=observer.on_completed,
                scheduler=scheduler)

        return rx.create(subscribe)

    return _query_and_transform


def init_tweepy_client() -> Client:
    # consumer key and secret represents the Twitter's authorization about calling its API
    api_key, api_secret = get_consumer_key_and_secret()
    # access token pair to represent the user's authorization about operating the account
    access_token, access_token_secret = get_access_token_and_secret(api_key, api_secret)

    # It's ok (secure) to save them into env, document isn't mention that,
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


def save_secrets_to_env(api_key, api_secret, access_token, access_token_secret):
    os.environ[API_KEY] = api_key
    os.environ[API_KEY_SECRET] = api_secret
    os.environ[ACCESS_TOKEN] = access_token
    os.environ[ACCESS_TOKEN_SECRET] = access_token_secret


def get_access_token_and_secret(api_key, api_secret):
    access_token, access_token_secret = get_access_token_pair_from_env()
    if access_token and access_token_secret:
        print('Got the access token and secret from environment variables.')
        return access_token, access_token_secret
    else:
        return get_access_token_pair_via_authorization_pin(api_key, api_secret)


def get_access_token_pair_via_authorization_pin(api_key, api_secret):
    oauth1_user_handler = OAuth1UserHandler(api_key, api_secret, callback='oob')

    print('Now you need to authorize your app to access your Twitter account\n'
          'by entering the PIN code you get from newly opened browser window:\n'
          + oauth1_user_handler.get_authorization_url() + '\n')

    pin = util.get_input_from_terminal('PIN')
    return oauth1_user_handler.get_access_token(pin)


def get_access_token_pair_from_env():
    return os.environ.get(ACCESS_TOKEN), os.environ.get(ACCESS_TOKEN_SECRET)


def get_consumer_key_and_secret():
    api_key, api_secret = get_consumer_key_pair_from_env()
    if api_key and api_secret:
        print('Got the Dev API key and secret from environment variables.')
        return api_key, api_secret
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
