import binascii
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey

from puntgun import util
from puntgun.conf import config
from puntgun.conf.encrypto import encrypt, decrypt, generate_or_load_private_key

# names of secrets in the secret settings file
twitter_api_key_name = 'API_KEY'
twitter_api_secret_name = 'API_SECRET'
twitter_access_token_name = 'ACCESS_TOKEN'
twitter_access_token_secret_name = 'ACCESS_TOKEN_SECRET'


class TwitterAPISecrets(object):
    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret

    @staticmethod
    def from_environment(dynaconf_settings=config.settings):
        return TwitterAPISecrets(load_settings_from_environment_variables(twitter_api_key_name, dynaconf_settings),
                                 load_settings_from_environment_variables(twitter_api_secret_name, dynaconf_settings))

    @staticmethod
    def from_settings(dynaconf_settings=config.settings):
        pri_key = generate_or_load_private_key()
        return TwitterAPISecrets(
            load_and_decrypt_secret_from_settings(pri_key, twitter_api_key_name, dynaconf_settings),
            load_and_decrypt_secret_from_settings(pri_key, twitter_api_secret_name, dynaconf_settings))

    @staticmethod
    def from_input():
        print('We need a "Twitter Dev OAuth App API" to start.\n'
              'You can get one by signing up on [ https://developer.twitter.com/en ] for free'
              ' if you have a twitter account,\n'
              'but it requires you to bind a phone number with the account.\n'
              '(You can unbind that after signed up Dev API)\n\n'
              'And don\'t forget to turn on OAuth 1.0a in your App settings:\n'
              '  1. Set the App permissions to "Read and write".\n'
              '  2. Set the callback, website URL to "https://twitter.com" for passing'
              ' the website\'s validation check.\n\n'
              'We\'ll use the pin based auth method, so we needn\'t really deploy a server for'
              ' receiving Twitter\'s callback.\n'
              '-> https://developer.twitter.com/en/docs/authentication/oauth-1-0a/pin-based-oauth\n\n'
              'Feel free to terminate me if you don\'t want to register right now.\n'
              'Don\'t forget to clean the clipboard after copying and pasting secrets to here.')

        return TwitterAPISecrets(util.get_input_from_terminal('Api key'), util.get_input_from_terminal('Api secret'))


# == low level ==

def load_settings_from_environment_variables(name: str, dynaconf_settings=config.settings):
    """
    Secrets stored as environment variables can be loaded by dynaconf.
    In this case they are stored in plaintext.
    """
    return dynaconf_settings[f'{name}']


def load_and_decrypt_secret_from_settings(private_key: RSAPrivateKey, name: str, dynaconf_settings=config.settings):
    return decrypt(private_key, binascii.unhexlify(dynaconf_settings[name]))


def encrypt_and_save_secrets_into_file(public_key: RSAPublicKey,
                                       file_path: Path = config.secrets_config_file_path,
                                       **kwargs):
    """
    Will overwrite the file if it already exists.
    Save encrypted bytes as hex format.
    """

    def transform(msg):
        return binascii.hexlify(encrypt(public_key, msg)).decode('utf-8')

    with open(file_path, 'w', encoding='utf-8') as f:
        # if we do not add '\n' at the tail, all items are printed into one line
        f.writelines(f'{key}: {transform(value)}\n' for key, value in kwargs.items())
