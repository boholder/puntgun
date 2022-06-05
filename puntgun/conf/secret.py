import binascii
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey

from puntgun.conf.config import config_dir_path, settings
from puntgun.conf.encrypto import encrypt, decrypt

# encrypted secrets are stored into this file
secrets_config_file_path = config_dir_path.joinpath('.secrets.yml')


def load_and_decrypt_secret_from_settings(private_key: RSAPrivateKey, name: str, dynaconf_settings=settings):
    return decrypt(private_key, binascii.unhexlify(dynaconf_settings[name]))


def encrypt_and_save_secrets_into_file(public_key: RSAPublicKey,
                                       file_path: Path = secrets_config_file_path,
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
