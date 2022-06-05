from unittest.mock import Mock

import pytest
import tweepy
from dynaconf import Dynaconf

from puntgun.conf.encrypto import generate_private_key
from puntgun.conf.secret import encrypt_and_save_secrets_into_file, load_and_decrypt_secret_from_settings, \
    load_or_request_api_secrets, load_or_request_access_token_secrets, TwitterAPISecrets


def test_secrets_save_and_load_via_settings_file(tmp_path):
    private_key = generate_private_key()
    # the settings file must be the dynaconf recognizable file type
    path = tmp_path.joinpath('secrets.yml')
    # save to file
    encrypt_and_save_secrets_into_file(private_key.public_key(), path, a='token', b='another')
    # read from file (via settings)
    settings = Dynaconf(settings_files=str(path.absolute()))
    assert load_and_decrypt_secret_from_settings(private_key, 'a', settings) == 'token'
    assert load_and_decrypt_secret_from_settings(private_key, 'b', settings) == 'another'


@pytest.fixture
def mock_secret_config_file(mock_private_key_file, monkeypatch, tmp_path):
    secrets_setting_file = tmp_path.joinpath('s.yml')
    # load the private key for decrypt secrets
    monkeypatch.setattr('builtins.input', Mock(side_effect=['pwd', 'y']))
    # change the settings to load test configuration file
    monkeypatch.setattr('puntgun.conf.secret.load_and_decrypt_secret_from_settings.__defaults__',
                        (Dynaconf(settings_files=str(secrets_setting_file.absolute())),))

    def func(**kwargs):
        encrypt_and_save_secrets_into_file(mock_private_key_file[1].public_key(), secrets_setting_file, **kwargs)

    return func


class TestLoadApiSecretsInteractively:

    def test_from_env(self, monkeypatch):
        monkeypatch.setenv('BULLET_AK', 'key')
        monkeypatch.setenv('BULLET_AKS', 'secret')
        self.assert_result()

    def test_from_settings(self, mock_secret_config_file):
        mock_secret_config_file(ak='key', aks='secret')
        self.assert_result()

    def test_from_input(self, monkeypatch, mock_private_key_file):
        # load the private key, then enter two secrets
        monkeypatch.setattr('builtins.input', Mock(side_effect=['pwd', 'y', 'key', 'y', 'secret', 'y']))
        self.assert_result()

    @staticmethod
    def assert_result():
        actual = load_or_request_api_secrets()
        assert actual.key == 'key'
        assert actual.secret == 'secret'


class TestLoadAccessTokenSecretsInteractively:

    def test_load_from_env(self, monkeypatch):
        monkeypatch.setenv('BULLET_AT', 'key')
        monkeypatch.setenv('BULLET_ATS', 'secret')
        self.assert_result()

    def test_load_from_settings(self, mock_secret_config_file):
        mock_secret_config_file(at='key', ats='secret')
        self.assert_result()

    def test_from_input(self, monkeypatch, mock_private_key_file):
        # load the private key, then enter the pin
        monkeypatch.setattr('builtins.input', Mock(side_effect=['pwd', 'y', 'PIN-PIN-PIN', 'y']))
        monkeypatch.setattr(tweepy.auth.OAuth1UserHandler, 'get_authorization_url', lambda _: 'url-here')
        monkeypatch.setattr(tweepy.auth.OAuth1UserHandler, 'get_access_token', lambda _, __: ('key', 'secret'))
        self.assert_result()

    @staticmethod
    def assert_result():
        actual = load_or_request_access_token_secrets(TwitterAPISecrets('123', '456'))
        assert actual.token == 'key'
        assert actual.secret == 'secret'
