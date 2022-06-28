import binascii
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey
from loguru import logger
from pydantic import BaseModel
from tweepy import OAuth1UserHandler

import util
from conf import config
from conf.encrypto import encrypt, decrypt, load_or_generate_public_key, load_or_generate_private_key

# names of secrets in the secret settings file
twitter_api_key_name = 'AK'
twitter_api_key_secret_name = 'AKS'
twitter_access_token_name = 'AT'
twitter_access_token_secret_name = 'ATS'


class TwitterAPISecrets(BaseModel):
    key: str
    secret: str

    class Config:
        # Checking the length is a trick:
        #
        # Both loading secrets from environment variables and from setting file
        # are involved using dynaconf library, and secrets keys in two ways are same after dynaconf loading.
        # (from env: BULLET_SEC --dynaconf--> sec, from settings: SEC --dynaconf--> sec)
        #
        # So dynaconf couldn't recognize where the secrets from,
        # but in env var secrets are plaintext format while in settings file are cipher text.
        #
        # Thankfully these two format have a significant difference - the length.
        # plaintexts length are below 50 characters, but I'll set to 100 for compatibility.
        max_anystr_length = 100

    @staticmethod
    def from_environment():
        return TwitterAPISecrets(key=load_settings_from_environment_variables(twitter_api_key_name),
                                 secret=load_settings_from_environment_variables(twitter_api_key_secret_name))

    @staticmethod
    def from_settings(pri_key: RSAPrivateKey):
        return TwitterAPISecrets(key=load_and_decrypt_secret_from_settings(pri_key, twitter_api_key_name),
                                 secret=load_and_decrypt_secret_from_settings(pri_key, twitter_api_key_secret_name))

    @staticmethod
    def from_input():
        print("""
Now we need a "Twitter Dev OAuth App API" to continue.
With this, we can request the developer APIs provided by Twitter.
You can get one by signing up on link below for free if you have a Twitter account.

https://developer.twitter.com/en
    
And it requires you to bind a phone number with that account.
You can do unbind after get the credential, and the credential will remain valid.

And don't forget to turn on OAuth 1.0a in your App settings:

  1. Set the App permissions to "Read and write".
  
  2. Set the callback, website URL to "https://twitter.com" for passing
     the website's validation check.
     (We'll use the pin based auth method, so we needn't really deploy a server for
     receiving Twitter's callback.)
     
     https://developer.twitter.com/en/docs/authentication/oauth-1-0a/pin-based-oauth
     
Feel free to terminate this tool if you don't want to register right now.
(Don't forget to clean the clipboard after copying and pasting secrets to here.)
""")

        return TwitterAPISecrets(key=util.get_input_from_terminal('Api key'),
                                 secret=util.get_input_from_terminal('Api key secret'))


class TwitterAccessTokenSecrets(BaseModel):
    token: str
    secret: str

    class Config:
        max_anystr_length = 100

    @staticmethod
    def from_environment():
        return TwitterAccessTokenSecrets(token=load_settings_from_environment_variables(twitter_access_token_name),
                                         secret=load_settings_from_environment_variables(
                                             twitter_access_token_secret_name))

    @staticmethod
    def from_settings(pri_key: RSAPrivateKey):
        return TwitterAccessTokenSecrets(
            token=load_and_decrypt_secret_from_settings(pri_key, twitter_access_token_name),
            secret=load_and_decrypt_secret_from_settings(pri_key, twitter_access_token_secret_name))

    @staticmethod
    def from_input(api_secrets: TwitterAPISecrets):
        oauth1_user_handler = OAuth1UserHandler(api_secrets.key, api_secrets.secret, callback='oob')

        print(f"""
We've gotten a pair of API secrets. Cool. But we still need to do one last thing:
tell Twitter you allowed this API secrets pair to operate your account 
(which is indispensable for executing block operation etc.). How?
We just used the API secrets to request Twitter and Twitter returned back an link.

{oauth1_user_handler.get_authorization_url()}

Same as other third-party authentication agreement,
you'll see a number series called "PIN code" when you open the link,
enter them back to here. Again, feel free to terminate this tool if you don't want to continue.
""")

        pin = util.get_input_from_terminal('PIN')
        token_pair = oauth1_user_handler.get_access_token(pin)
        return TwitterAccessTokenSecrets(token=token_pair[0], secret=token_pair[1])


def load_or_request_all_secrets(pri_key):
    api_secrets = load_or_request_api_secrets(pri_key)
    access_token_secrets = load_or_request_access_token_secrets(api_secrets, pri_key)

    # Save the secrets into file if they are not saved yet.
    # Must save them at once because saving method will override the existing file.
    if not secrets_config_file_valid():
        print(f"""
Before running plans, we'd save secrets into a secret configuration file,
so next time you running this tool you needn't enter these annoying unreadable tokens again.
And we'll encrypt them before saving, it's time to load your private key.   
""")
        encrypt_and_save_secrets_into_file(load_or_generate_public_key(),
                                           config.secrets_config_file_path,
                                           **{twitter_api_key_name: api_secrets.key,
                                              twitter_api_key_secret_name: api_secrets.secret,
                                              twitter_access_token_name: access_token_secrets.token,
                                              twitter_access_token_secret_name: access_token_secrets.secret
                                              })
        print(f"Secrets saved into file.\n({config.secrets_config_file_path})")
    return {'ak': api_secrets.key,
            'aks': api_secrets.secret,
            'at': access_token_secrets.token,
            'ats': access_token_secrets.secret}


def load_or_request_api_secrets(pri_key: RSAPrivateKey = None):
    try:
        return TwitterAPISecrets.from_environment()
    except ValueError:
        logger.info("Failed to load api secrets from environment")

    if secrets_config_file_valid():
        logger.info("Found previous secrets config file")
        try:
            if not pri_key:
                pri_key = load_or_generate_private_key()
            return TwitterAPISecrets.from_settings(pri_key)
        except (ValueError, TypeError):
            logger.info("Failed to load api secrets from settings, trying to get API secrets from input")

    return TwitterAPISecrets.from_input()


def load_or_request_access_token_secrets(api_secrets: TwitterAPISecrets, pri_key: RSAPrivateKey = None):
    try:
        return TwitterAccessTokenSecrets.from_environment()
    except ValueError:
        logger.info('Failed to load access token secrets from environment')

    if secrets_config_file_valid():
        logger.info("Found previous secrets config file")
        try:
            if not pri_key:
                pri_key = load_or_generate_private_key()
            return TwitterAccessTokenSecrets.from_settings(pri_key)
        except (ValueError, TypeError):
            logger.info("Failed to load access token secrets from settings,"
                        " trying to get access token secrets from input")

    # here we need the api secrets to generate new access token.
    return TwitterAccessTokenSecrets.from_input(api_secrets)


# == low level ==

def load_settings_from_environment_variables(name: str, dynaconf_settings=None):
    """
    Secrets stored as environment variables can be loaded by dynaconf.
    In this case they are stored in plaintext.
    """
    if not dynaconf_settings:
        dynaconf_settings = config.settings
    return dynaconf_settings.get(name)


def load_and_decrypt_secret_from_settings(private_key: RSAPrivateKey, name: str, dynaconf_settings=None):
    if not dynaconf_settings:
        dynaconf_settings = config.settings
    return decrypt(private_key, binascii.unhexlify(dynaconf_settings.get(name)))


def encrypt_and_save_secrets_into_file(public_key: RSAPublicKey,
                                       file_path: Path = config.secrets_config_file_path,
                                       **kwargs):
    """
    Will overwrite the file if already exists.
    Save the encrypted bytes as hex format into a file.
    """

    def transform(msg):
        return binascii.hexlify(encrypt(public_key, msg)).decode('utf-8')

    with open(file_path, 'w', encoding='utf-8') as f:
        # if we do not add '\n' at the tail, all items are printed into one line
        f.writelines(f'{key}: {transform(value)}\n' for key, value in kwargs.items())


def secrets_config_file_valid():
    def not_empty_or_has_only_blank_characters():
        with open(config.secrets_config_file_path, 'r', encoding='utf-8') as f:
            return bool(f.read().strip())

    return config.secrets_config_file_path.exists() and not_empty_or_has_only_blank_characters()
