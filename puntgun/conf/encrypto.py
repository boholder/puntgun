"""Methods that access, modify, and save secrets that need to be encrypted, as well as private key itself."""
import functools
import sys

from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey
from loguru import logger

import util
from conf import config

encrypt_padding = padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)


@functools.lru_cache(maxsize=1)
def load_or_generate_public_key():
    """For encrypting secrets."""
    return load_or_generate_private_key().public_key()


def load_or_generate_private_key():
    """For decrypting secrets."""

    def load_with_password_from_prompt():
        """Trying different passwords in an infinity loop till the user get bored."""
        err_count = 0
        while True:
            if err_count > 2:
                print('Maybe you want to reset the password as described above.')
            try:
                private_key = load_private_key(util.get_input_from_terminal('Password'), config.pri_key_file)
                logger.info("Private key file loaded with correct password")
                return private_key
            except ValueError:
                err_count += 1
                print('Incorrect password.')

    def load_with_password_from_stdin():
        return load_private_key("".join(sys.stdin.readlines()), config.pri_key_file)

    def generate_and_save():
        pwd = util.get_input_from_terminal('Password')
        pri_key = generate_private_key()
        dump_private_key(pri_key, pwd, config.pri_key_file)
        print(f'The private key has been saved into the file'
              f'({config.pri_key_file}).')
        return pri_key

    # == start logic ==
    if config.pri_key_file.exists():
        print(f"""
Found the previous saved private key file. 
({config.pri_key_file})
Now please enter the password.

If you've forget the password, just delete the private key file and the secrets file
({config.secrets_file}) 
and rerun this tool for initializing things again.
""")

        logger.info("Found the existing private key, trying to load with password")
        if config.settings.get('read_password_from_stdin', False):
            return load_with_password_from_stdin()
        else:
            return load_with_password_from_prompt()

    else:
        print(f"""
It seems that you have not generated a private key for encrypting secrets before.
Let's generate one for you, 
but we need you to set a password for protecting that private key.
The strength of this password should be the same as your Twitter account password.
It would be better if you set a different password from the Twitter password.  
And you should remember this password for using this tool in the future.

If you can not remember it, 
just delete the private key file and the secrets file and run it again.
({config.pri_key_file}, {config.secrets_file})
""")

        logger.info("Generated a new private key")
        return generate_and_save()


# == low level ==

def encrypt(pub_key: RSAPublicKey, plaintext: str):
    return pub_key.encrypt(bytes(plaintext, 'utf-8'), encrypt_padding)


def decrypt(pri_key: RSAPrivateKey, ciphertext: bytes):
    return pri_key.decrypt(ciphertext, encrypt_padding).decode('utf-8')


def dump_private_key(pri_key: RSAPrivateKey, pwd: str, file_path):
    """will overwrite the file if it already exists"""
    util.backup_if_exists(file_path)
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


def load_private_key(pwd: str, file_path):
    with open(file_path, 'rb') as f:
        return serialization.load_pem_private_key(f.read(), password=bytes(pwd, 'utf-8'))


def generate_private_key():
    # https://crypto.stackexchange.com/questions/19458/what-is-the-difference-between-secp-and-sect
    return rsa.generate_private_key(public_exponent=65537, key_size=4096)
