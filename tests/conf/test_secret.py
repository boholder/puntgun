import pytest
import tweepy
from dynaconf import Dynaconf

from puntgun.conf import encrypto, secret
from puntgun.conf.secret import TwitterAPISecrets


@pytest.fixture(autouse=True)
def clean_config_env(monkeypatch, tmp_path):
    """
    Make the unit test cases not affected by host's configuration environment.
    (Make configuration files not exist from view of the test cases.)
    """
    monkeypatch.setattr('puntgun.conf.config.pri_key_file', tmp_path.joinpath('1'))
    monkeypatch.setattr('puntgun.conf.config.secrets_file', tmp_path.joinpath('2'))


def test_secrets_save_and_load_via_settings_file(tmp_path):
    private_key = encrypto.generate_private_key()
    # the settings file must be the dynaconf recognizable file type
    path = tmp_path.joinpath('secrets.yml')
    # save to file
    secret.encrypt_and_save_secrets_into_file(private_key.public_key(), path, a='token', b='another')
    # read from file (via settings)
    settings = Dynaconf(settings_files=path)
    assert secret.load_and_decrypt_secret_from_settings(private_key, 'a', settings) == 'token'
    assert secret.load_and_decrypt_secret_from_settings(private_key, 'b', settings) == 'another'


def test_secrets_config_file_exists_check(monkeypatch, tmp_path):
    fake_secrets_setting_file = tmp_path.joinpath('s.yml')
    monkeypatch.setattr('puntgun.conf.config.secrets_file', fake_secrets_setting_file)

    def save_content_to_file(content):
        with open(fake_secrets_setting_file, 'w', encoding='utf-8') as f:
            f.write(content)

    # blank = invalid
    save_content_to_file('   \n\t')
    assert secret.secrets_config_file_valid() is False
    # has content = valid
    save_content_to_file('not empty')
    assert secret.secrets_config_file_valid() is True
    # not exist = invalid
    monkeypatch.setattr('puntgun.conf.config.secrets_file', tmp_path.joinpath('b.yml'))
    assert secret.secrets_config_file_valid() is False


@pytest.fixture
def mock_secrets_config_file(mock_private_key_file, monkeypatch, tmp_path, mock_input):
    secrets_setting_file = tmp_path.joinpath('s.yml')
    # load the private key for decrypt secrets
    mock_input('pwd', 'y')
    # change the settings to load test configuration file
    monkeypatch.setattr('puntgun.conf.config.secrets_file', secrets_setting_file)
    monkeypatch.setattr('puntgun.conf.config.settings', Dynaconf(settings_files=secrets_setting_file))

    def save_content_to_file(**kwargs):
        secret.encrypt_and_save_secrets_into_file(mock_private_key_file[1].public_key(), secrets_setting_file, **kwargs)

    return save_content_to_file


class TestLoadApiSecretsInteractively:

    def test_load_from_env(self, monkeypatch, tmp_path, mock_configuration):
        monkeypatch.setenv('BULLET_AK', 'key')
        monkeypatch.setenv('BULLET_AKS', 'secret')
        # avoid real existing secret config file's disturbance
        # let dynaconf reload environment variables
        mock_configuration(Dynaconf(envvar_prefix='BULLET'))
        self.assert_result()

    def test_load_from_settings(self, mock_secrets_config_file):
        mock_secrets_config_file(ak='key', aks='secret')
        self.assert_result()

    def test_load_from_input(self, monkeypatch, mock_input):
        # mock_secrets_config_file for letting program believes there is no valid secrets config file,
        # so it won't try to load private key for decrypting secrets config file --
        # which leads to requiring password input and fail the test.
        mock_input('key', 'y', 'secret', 'y')
        self.assert_result()

    @staticmethod
    def assert_result():
        actual = secret.load_or_request_api_secrets()
        assert actual.key == 'key'
        assert actual.secret == 'secret'


class TestLoadAccessTokenSecretsInteractively:

    def test_load_from_env(self, monkeypatch, tmp_path, mock_configuration):
        monkeypatch.setenv('BULLET_AT', 'key')
        monkeypatch.setenv('BULLET_ATS', 'secret')
        # avoid real existing secret config file's disturbance
        # let dynaconf reload environment variables
        mock_configuration(Dynaconf(envvar_prefix='BULLET'))
        self.assert_result()

    def test_load_from_settings(self, mock_secrets_config_file):
        mock_secrets_config_file(at='key', ats='secret')
        self.assert_result()

    def test_load_from_input(self, monkeypatch, mock_input):
        # load the private key, then enter the pin
        mock_input('pwd', 'y', 'PIN-PIN-PIN', 'y')
        monkeypatch.setattr(tweepy.auth.OAuth1UserHandler, 'get_authorization_url', lambda _: 'url-here')
        monkeypatch.setattr(tweepy.auth.OAuth1UserHandler, 'get_access_token', lambda _, __: ('key', 'secret'))
        self.assert_result()

    @staticmethod
    def assert_result():
        actual = secret.load_or_request_access_token_secrets(TwitterAPISecrets(key='123', secret='456'))
        assert actual.token == 'key'
        assert actual.secret == 'secret'
