import os
from typing import List, Union

from tweepy import User, Client, OAuth1UserHandler, Tweet

API_KEY = 'TWI_API_KEY'
API_KEY_SECRET = 'TWI_API_KEY_SECRET'
ACCESS_TOKEN = 'TWI_ACCESS_TOKEN'
ACCESS_TOKEN_SECRET = 'TWI_ACCESS_TOKEN_SECRET'


class Hunter:
    user_fields = ['id', 'name', 'username', 'created_at', 'description',
                   'pinned_tweet_id', 'public_metrics', 'protected',
                   'verified']

    def __init__(self):
        self.client = init_tweepy_client()
        me = self.client.get_me().data
        self.id = me.get('id')
        self.username = me.get('username')

        print('[{}] the hunter dressed up.\n'.format(self.username))

    def observe(self, user_id='', username='', user_ids=None) -> Union[User, List[User]]:
        """Get user(s) information from Twitter."""
        if user_id:
            return self.client.get_user(id=user_id, user_auth=True, user_fields=Hunter.user_fields).data
        elif username:
            return self.client.get_user(username=username, user_auth=True, user_fields=Hunter.user_fields).data
        elif user_ids:
            return [self.observe(user_id=user_id) for user_id in user_ids]
        else:
            raise ValueError('No value provided.')

    def trace(self, user_id='', user_ids=None, **params) -> List[Tweet]:
        return self.client.search_recent_tweets(query="from:{}".format(user_id), user_auth=True)


# class Trace:
#     def __init__(self, user: User):
#


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

    pin = get_input('PIN')
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

    return get_input('Api key'), get_input('Api secret')


def get_input(key: str) -> str:
    key_loop = True
    value = ''
    while key_loop:
        value = input('{}:'.format(key))
        # default yes
        confirm = input('confirm?([y]/n)')
        if not confirm or confirm.lower() == 'y':
            key_loop = False

    return value
