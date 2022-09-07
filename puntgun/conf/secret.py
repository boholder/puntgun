import binascii
from pathlib import Path
from typing import Dict

import dynaconf
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey
from loguru import logger
from pydantic import BaseModel
from tweepy import OAuth1UserHandler

from puntgun import util
from puntgun.conf import config, encrypto

# names of secrets in the secret settings file
twitter_api_key_name = "AK"
twitter_api_key_secret_name = "AKS"
twitter_access_token_name = "AT"
twitter_access_token_secret_name = "ATS"

GET_API_SECRETS_FROM_INPUT = """Now we need a "Twitter Dev OAuth App API" to continue.
With this, we can request the developer APIs provided by Twitter.
You can get one by signing up on link below for free if you have a Twitter account.

https://developer.twitter.com/en

And it requires you to bind a phone number with that account.
You can do unbind after get the credential, and the credential will remain valid.

And do not forget to turn on OAuth 1.0a in your App settings:

  1. Set the App permissions to "Read and write".

  2. Set the callback, website URL to "https://twitter.com" for passing
     the website's validation check.
     (We'll use the pin based auth method, so we need not really deploy a server for
     receiving Twitter's callback.)

     https://developer.twitter.com/en/docs/authentication/oauth-1-0a/pin-based-oauth

Feel free to terminate this tool if you do not want to register right now.
(Do not forget to clean the clipboard after copying and pasting secrets to here.)"""


class TwitterAPISecrets(BaseModel):
    key: str
    secret: str

    class Config:
        # IMPROVE: Checking the length is a trick:
        #
        # Both loading secrets from environment variables and from setting file
        # are involved using dynaconf library, and secrets keys in two ways are same after dynaconf loading.
        # (from env: BULLET_SEC --dynaconf--> sec, from settings: SEC --dynaconf--> sec)
        #
        # So we couldn't recognize where the secrets from through dynaconf,
        # but in env var secrets are plaintext format while in settings file are ciphertext.
        #
        # Thankfully these two format have a significant difference - the length.
        # plaintexts length are below 50 characters, but I'll set to 100 for compatibility.
        max_anystr_length = 100

    @staticmethod
    def from_environment() -> "TwitterAPISecrets":
        return TwitterAPISecrets(
            key=load_settings_from_environment_variables(twitter_api_key_name),
            secret=load_settings_from_environment_variables(twitter_api_key_secret_name),
        )

    @staticmethod
    def from_settings(pri_key: RSAPrivateKey) -> "TwitterAPISecrets":
        return TwitterAPISecrets(
            key=load_and_decrypt_secret_from_settings(pri_key, twitter_api_key_name),
            secret=load_and_decrypt_secret_from_settings(pri_key, twitter_api_key_secret_name),
        )

    @staticmethod
    def from_input() -> "TwitterAPISecrets":
        print(GET_API_SECRETS_FROM_INPUT)
        return TwitterAPISecrets(
            key=util.get_secret_from_terminal("Api key"), secret=util.get_secret_from_terminal("Api key secret")
        )


AUTH_URL = """We have gotten a pair of API secrets. Cool. But we still need to do one last thing:
tell Twitter you allowed this API secrets pair to operate your account
(which is indispensable for executing block operation etc.). How?
We just used the API secrets to request Twitter and Twitter returned a link.

{auth_url}

Same as other third-party authentication agreement,
you'll see a number sequence called "PIN code" when you open the link,
enter them back to here. Again, feel free to terminate this tool if you do not want to continue.
"""


class TwitterAccessTokenSecrets(BaseModel):
    token: str
    secret: str

    class Config:
        max_anystr_length = 100

    @staticmethod
    def from_environment() -> "TwitterAccessTokenSecrets":
        return TwitterAccessTokenSecrets(
            token=load_settings_from_environment_variables(twitter_access_token_name),
            secret=load_settings_from_environment_variables(twitter_access_token_secret_name),
        )

    @staticmethod
    def from_settings(pri_key: RSAPrivateKey) -> "TwitterAccessTokenSecrets":
        return TwitterAccessTokenSecrets(
            token=load_and_decrypt_secret_from_settings(pri_key, twitter_access_token_name),
            secret=load_and_decrypt_secret_from_settings(pri_key, twitter_access_token_secret_name),
        )

    @staticmethod
    def from_input(api_secrets: TwitterAPISecrets) -> "TwitterAccessTokenSecrets":
        oauth1_user_handler = OAuth1UserHandler(api_secrets.key, api_secrets.secret, callback="oob")
        print(AUTH_URL.format(auth_url=oauth1_user_handler.get_authorization_url()))
        pin = util.get_input_from_terminal("PIN")
        token_pair = oauth1_user_handler.get_access_token(pin)
        return TwitterAccessTokenSecrets(token=token_pair[0], secret=token_pair[1])


SAVE_SECRETS = """Before running plans, we'd save secrets into a secret configuration file,
so next time you running this tool you need not enter these annoying unreadable tokens again.
And we'll encrypt them before saving, it's time to load your private key."""


def load_or_request_all_secrets(pri_key: RSAPrivateKey) -> Dict[str, str]:
    api_secrets = load_or_request_api_secrets(pri_key)
    access_token_secrets = load_or_request_access_token_secrets(api_secrets, pri_key)
    secrets = {
        "ak": api_secrets.key,
        "aks": api_secrets.secret,
        "at": access_token_secrets.token,
        "ats": access_token_secrets.secret,
    }

    # Save the secrets into file if they are not saved yet.
    # Must save them at once because saving method will override the existing file.
    if not secrets_config_file_valid():
        print(SAVE_SECRETS)
        encrypt_and_save_secrets_into_file(encrypto.load_or_generate_public_key(), config.secrets_file, **secrets)
        logger.bind(o=True).info(f"Secrets saved into file:\n({config.secrets_file})")

    return secrets


def load_or_request_api_secrets(pri_key: RSAPrivateKey = None) -> TwitterAPISecrets:
    try:
        return TwitterAPISecrets.from_environment()
    except ValueError:
        logger.info("Failed to load api secrets from environment")

    if secrets_config_file_valid():
        logger.info("Found previous secrets config file")
        try:
            # you may wander why not use default value on function parameter.
            # That's for unit test conveniences,
            # because python initializes methods' signatures pretty early on running,
            # and if you want to mock default parameters to another values,
            # you need to do mock on each method, even all origin default values are
            # from same one function. (e.g. this "load_or_generate_private_key" )
            #
            # By changing default values assignments to this none checking form,
            # you only need to mock that exactly function.
            if not pri_key:
                pri_key = encrypto.load_or_generate_private_key()
            return TwitterAPISecrets.from_settings(pri_key)
        except (ValueError, TypeError):
            logger.info("Failed to load api secrets from settings, trying to get API secrets from input")

    return TwitterAPISecrets.from_input()


def load_or_request_access_token_secrets(
    api_secrets: TwitterAPISecrets, pri_key: RSAPrivateKey = None
) -> TwitterAccessTokenSecrets:
    try:
        return TwitterAccessTokenSecrets.from_environment()
    except ValueError:
        logger.info("Failed to load access token secrets from environment")

    if secrets_config_file_valid():
        logger.info("Found previous secrets config file")
        try:
            if not pri_key:
                pri_key = encrypto.load_or_generate_private_key()
            return TwitterAccessTokenSecrets.from_settings(pri_key)
        except (ValueError, TypeError):
            logger.info(
                "Failed to load access token secrets from settings, trying to get access token secrets from input"
            )

    # here we need the api secrets to generate new access token.
    return TwitterAccessTokenSecrets.from_input(api_secrets)


# == low level ==


def load_settings_from_environment_variables(name: str, dynaconf_settings: dynaconf.Dynaconf = None) -> str:
    """
    Secrets stored as environment variables can be loaded by dynaconf.
    In this case they are stored in plaintext.
    """
    if not dynaconf_settings:
        dynaconf_settings = config.settings
    return dynaconf_settings.get(name)


def load_and_decrypt_secret_from_settings(
    private_key: RSAPrivateKey, name: str, dynaconf_settings: dynaconf.Dynaconf = None
) -> str:
    if not dynaconf_settings:
        dynaconf_settings = config.settings
    return encrypto.decrypt(private_key, binascii.unhexlify(dynaconf_settings.get(name)))


def encrypt_and_save_secrets_into_file(
    public_key: RSAPublicKey, file_path: Path = config.secrets_file, **kwargs: str
) -> None:
    """
    Will overwrite the file if already exists.
    Save the encrypted bytes as hex format into a file.
    """

    def transform(msg: str) -> str:
        return binascii.hexlify(encrypto.encrypt(public_key, msg)).decode("utf-8")

    util.backup_if_exists(file_path)
    with open(file_path, "w", encoding="utf-8") as f:
        # if we do not add '\n' at the tail, all items are printed into one line
        f.writelines(f"{key}: {transform(value)}\n" for key, value in kwargs.items())


def secrets_config_file_valid() -> bool:
    def not_empty_or_has_only_blank_characters() -> bool:
        with open(config.secrets_file, "r", encoding="utf-8") as f:
            return bool(f.read().strip())

    return config.secrets_file.exists() and not_empty_or_has_only_blank_characters()
