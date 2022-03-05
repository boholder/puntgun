import os

import tweepy


class Hunter:
    def __init__(self):
        self.client = init_tweepy_client()
        self.me = self.client.get_me().data
        print('[{}] the hunter dressed up.\n'.format(self.me.get('username')))


def init_tweepy_client():
    # consumer key and secret represents the Twitter's authorization about calling its API
    api_key, api_secret, api_got_from_env = get_consumer_key_and_secret()
    # access token pair to represent the user's authorization about operating the account
    access_token, access_token_secret, token_got_from_env = get_access_token_and_secret(api_key, api_secret)

    # ask to save secrets to env if there are inputted secrets
    if not api_got_from_env or not token_got_from_env:
        if input('Save secrets to environment variables?(disappeared after reboot)\n'
                 '(y/n):').lower() == 'y':
            save_secrets_to_env(api_key, api_secret, access_token, access_token_secret)

    return tweepy.Client(consumer_key=api_key,
                         consumer_secret=api_secret,
                         access_token=access_token,
                         access_token_secret=access_token_secret)


def save_secrets_to_env(api_key, api_secret, access_token, access_token_secret):
    os.environ['TWI_API_KEY'] = api_key
    os.environ['TWI_API_SECRET'] = api_secret
    os.environ['TWI_ACCESS_TOKEN'] = access_token
    os.environ['TWI_ACCESS_TOKEN_SECRET'] = access_token_secret


def get_access_token_and_secret(api_key, api_secret):
    access_token, access_token_secret = get_access_token_pair_from_env()
    if access_token and access_token_secret:
        print('Got the access token and secret from environment variables.')
        return access_token, access_token_secret, True
    else:
        return get_access_token_pair_via_authorization_pin(api_key, api_secret), False


def get_access_token_pair_via_authorization_pin(api_key, api_secret):
    print('Now you need to authorize your app to access your Twitter account\n'
          'by entering the PIN code you get from newly opened browser window:')

    oauth1_user_handler = tweepy.OAuth1UserHandler(api_key, api_secret, callback='oob')
    print(oauth1_user_handler.get_authorization_url() + '\n')

    pin = get_input('PIN')
    return oauth1_user_handler.get_access_token(pin)


def get_access_token_pair_from_env():
    return os.environ.get('TWI_ACCESS_TOKEN'), os.environ.get('TWI_ACCESS_TOKEN_SECRET')


def get_consumer_key_and_secret():
    api_key, api_secret = read_consumer_key_pair_from_env()
    if api_key and api_secret:
        print('Got the Dev API key and secret from environment variables.')
        return api_key, api_secret, True
    else:
        return read_consumer_key_pair_from_input(), False


def read_consumer_key_pair_from_env():
    return os.environ.get('TWI_API_KEY'), os.environ.get('TWI_API_KEY_SECRET')


def read_consumer_key_pair_from_input():
    print('We need a pair of Twitter Dev OAuth Consumer API Key and Secret to start.\n'
          'You can get one by signing up on https://developer.twitter.com/en for free,\n'
          'but you need to bind a phone number with your account\n'
          '(can unbind it after signed up dev api :P)\n')

    return get_input('Key'), get_input('Secret')


def get_input(key: str):
    key_loop = True
    while key_loop:
        value = input('{}:'.format(key))
        confirm = input('confirm?(y/n)')
        key_loop = not confirm.lower() == 'y'
    return value
