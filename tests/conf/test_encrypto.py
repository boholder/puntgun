from from_root import from_here
from puntgun.conf.encrypto import generate_private_key, dump_private_key, load_private_key, encrypt, decrypt


def test_all_cryptographic_methods():
    path = from_here('test_pri_key_file')
    origin_key = generate_private_key()
    dump_private_key(origin_key, 'pwd', path)
    loaded_key = load_private_key('pwd', path)

    c = encrypt(loaded_key.public_key(), 'text')
    p = decrypt(origin_key, c)
    assert 'text' == p
