from dynaconf import Dynaconf
from from_root import from_here

from puntgun.conf.encrypto import generate_private_key
from puntgun.conf.secret import encrypt_and_save_secrets_into_file, load_and_decrypt_secret_from_settings


def test_secrets_save_and_load_via_file():
    private_key = generate_private_key()
    path = from_here('test_secret_config_file.yml')
    # save to file
    encrypt_and_save_secrets_into_file(private_key.public_key(), path, a='token', b='another')
    # read from file (via settings)
    settings = Dynaconf(settings_files=str(path.absolute()))
    assert load_and_decrypt_secret_from_settings(private_key, 'a', settings) == 'token'
    assert load_and_decrypt_secret_from_settings(private_key, 'b', settings) == 'another'
