import functools
import os
from typing import List, Union

from tweepy import User, Client, OAuth1UserHandler, Tweet, Response

# keys for accessing twitter auth api secrets
from puntgun import util

NO_VALUE_PROVIDED = 'No value provided.'

API_KEY = 'TWI_API_KEY'
API_KEY_SECRET = 'TWI_API_KEY_SECRET'
ACCESS_TOKEN = 'TWI_ACCESS_TOKEN'
ACCESS_TOKEN_SECRET = 'TWI_ACCESS_TOKEN_SECRET'

# additional url params for querying Twitter user state api
USER_PARAM_USER_FIELDS = ['id', 'username', 'pinned_tweet_id',  # metadata
                          'created_at', 'description', 'public_metrics', 'protected', 'verified']  # metrics
USER_PARAM_EXPANSIONS = 'pinned_tweet_id'
USER_PARAM_TWITTER_FIELDS = ['text']  # metrics


class Hunter:
    """
    Handles the Twitter API via tweepy.
    Sort of like a DAO, wrapper of the resource accessing,
    and doesn't have decision logic.
    """
    logger = util.get_logger(__name__)

    @staticmethod
    @functools.lru_cache(maxsize=1)
    def instance() -> 'Hunter':
        """Get singleton instance of Hunter"""
        return Hunter()

    def __init__(self):
        """You should only get instance of this class via ``instance`` static method."""
        self.client = init_tweepy_client()

        me = self.client.get_me().data
        self.id = me.get('id')
        self.username = me.get('username')

        self.logger.info('[{}] the hunter dressed up.\n'.format(self.username))

    def observe(self, user_id='', username='', user_ids=None) -> Union[Response, List[Response]]:
        """Get user(s) information via Twitter Dev API.
        TODO 900 per 15min
        TODO 出错误码时tweepy的响应类型是什么?应该怎么定义我这些函数的响应类型？
        """

        def query(**params) -> Response:
            return self.client.get_user(
                user_auth=True,
                user_fields=USER_PARAM_USER_FIELDS,
                expansions=USER_PARAM_EXPANSIONS,
                twitter_fields=USER_PARAM_TWITTER_FIELDS,
                **params)

        if user_id:
            return query(user_id=user_id)
        elif username:
            return query(username=username)
        elif user_ids:
            return [self.observe(user_id=user_id) for user_id in user_ids]
        else:
            raise ValueError(NO_VALUE_PROVIDED)

    def find_feeding_place(self, user_id='') -> List[Tweet]:
        """Get user liked tweets via Twitter Dev API.
        TODO 75 per 15min
        """
        return self.client.get_liked_tweets(user_id)

    def listen_tweeting(self, **params) -> List[Tweet]:
        """Search for tweets via Twitter Dev API.
        TODO 180 per 15min
        """
        return self.client.search_recent_tweets(user_auth=True, **params)

    def shot_down(self, user_id='', user_ids=None) -> Union[bool, List[bool]]:
        """Block user via Twitter Dev API.
        TODO 50 per 15min
        """
        if user_id:
            return self.client.block(user_id).data.get("blocking")
        elif user_ids:
            return [self.shot_down(user_id=user_id) for user_id in user_ids]
        else:
            raise ValueError(NO_VALUE_PROVIDED)

    def ignore(self, user_id='', user_ids=None) -> Union[bool, List[bool]]:
        """Mute user via Twitter Dev API.
        TODO 50 per 15min
        """
        if user_id:
            return self.client.mute(user_id).data.get("muting")
        elif user_ids:
            return [self.ignore(user_id=user_id) for user_id in user_ids]
        else:
            raise ValueError(NO_VALUE_PROVIDED)

    def check_decoy(self, count=1) -> List[User]:
        """Get your followers ids via Twitter Dev API.
        TODO 15 per 15min
        TODO 返回的顺序是按时间asc还是desc?
        TODO 函数内部处理分页
        """
        return self.client.get_users_followers(self.id, user_auth=True)


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
          '(Can unbind the phone after signed up dev api)\n\n'
          'And don\'t forget to turn on OAuth 1.0a in your App settings:\n'
          '  1. Set the App permissions to "Read and write".\n'
          '  2. Set the callback, website URL to "https://twitter.com" for passing setting check.\n\n'
          'We\'ll use the pin based auth method, so we don\'t really need to deploy a server for callback.\n'
          '-> https://developer.twitter.com/en/docs/authentication/oauth-1-0a/pin-based-oauth\n\n')

    return util.get_input_from_terminal('Api key'), util.get_input_from_terminal('Api secret')
