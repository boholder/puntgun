# Methods that access, modify, and save secrets that need to be encrypted, as well as private key itself.
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey
from puntgun.conf.config import config_dir_str

pri_key_file_path = config_dir_str + '/.puntgun_rsa4096'

encrypt_padding = padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)


def encrypt(pub_key: RSAPublicKey, plaintext: str):
    return pub_key.encrypt(bytes(plaintext, 'utf-8'), encrypt_padding)


def decrypt(pri_key: RSAPrivateKey, ciphertext: bytes):
    return pri_key.decrypt(ciphertext, encrypt_padding).decode('utf-8')


def dump_private_key(file_path: str, pri_key: RSAPrivateKey, pwd: str):
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


def load_private_key(file_path: str, pwd: str):
    with open(file_path, 'rb') as f:
        return serialization.load_pem_private_key(f.read(), password=bytes(pwd, 'utf-8'))


def generate_private_key():
    # https://crypto.stackexchange.com/questions/19458/what-is-the-difference-between-secp-and-sect
    return rsa.generate_private_key(public_exponent=65537, key_size=4096)
