"""Methods that access, modify, and save secrets that need to be encrypted, as well as private key itself."""
import functools
from pathlib import Path

from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey
from loguru import logger

from puntgun import util
from puntgun.conf import config

encrypt_padding = padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)


# == high level functions includes interaction, it's hard to unit test them so skip testing them currently ==

@functools.lru_cache(maxsize=1)
def generate_or_load_public_key():
    """For encrypting secrets."""
    return generate_or_load_private_key().public_key()


def generate_or_load_private_key():
    """For decrypting secrets."""

    def load():
        """Trying different passwords in an infinity loop."""
        err_count = 0
        while True:
            if err_count > 2:
                print('Maybe you want to reset the password as described above.')
            try:
                logger.info("Private key file loaded with correct password")
                return load_private_key(util.get_input_from_terminal('Password'))
            except ValueError as _:
                err_count += 1
                print('Incorrect password.')

    def generate_and_save():
        pwd = util.get_input_from_terminal('Password')
        pri_key = generate_private_key()
        dump_private_key(pri_key, pwd)
        print(f'The private key has been saved into a file ({config.pri_key_file_str}).')
        return pri_key

    if config.pri_key_file_path.exists():
        print(f'Found the previous saved private key file ({config.pri_key_file_str}).\n'
              'Now enter the password.\n'
              f'If you\'ve forget the password, just delete the key file and the secrets file'
              f' ({str(config.secrets_config_file_path.absolute())}) and rerun for initializing things again.')

        logger.info("Found the existing private key, trying to load with password")
        return load()
    else:
        print('It seems that you haven\'t generated a private key for encrypting secrets before.\n'
              'Let me generate one for you, but I need you to set a password for protecting that private key.\n'
              'The strength of this password should be the same as your Twitter account password.\n'
              'And you should save this password for using this tool in the future.')

        logger.info("Generated a new private key")
        return generate_and_save()


# == low level ==

def encrypt(pub_key: RSAPublicKey, plaintext: str):
    return pub_key.encrypt(bytes(plaintext, 'utf-8'), encrypt_padding)


def decrypt(pri_key: RSAPrivateKey, ciphertext: bytes):
    return pri_key.decrypt(ciphertext, encrypt_padding).decode('utf-8')


def dump_private_key(pri_key: RSAPrivateKey, pwd: str, file_path: Path = config.pri_key_file_path):
    """will overwrite the file if it already exists"""
    with open(file_path, 'wb') as f:
        f.write(pri_key.private_bytes(
            # just some human-recognizable formats
            # https://stackoverflow.com/questions/1011572/convert-pem-key-to-ssh-rsa-format
            encoding=serialization.Encoding.PEM,
            # https://stackoverflow.com/questions/48958304/pkcs1-and-pkcs8-format-for-rsa-private-key
            # https://en.wikipedia.org/wiki/PKCS_8
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.BestAvailableEncryption(bytes(pwd, 'utf-8'))
        ))


def load_private_key(pwd: str, file_path: Path = config.pri_key_file_path):
    with open(file_path, 'rb') as f:
        return serialization.load_pem_private_key(f.read(), password=bytes(pwd, 'utf-8'))


def generate_private_key():
    # https://crypto.stackexchange.com/questions/19458/what-is-the-difference-between-secp-and-sect
    return rsa.generate_private_key(public_exponent=65537, key_size=4096)
