from from_root import from_here

import test_util
from puntgun.conf.encrypto import generate_private_key, dump_private_key, load_private_key, encrypt, decrypt


def test_all_cryptographic_methods():
    path = from_here(test_util.take_one_unique_test_file_name())
    origin_key = generate_private_key()
    dump_private_key(origin_key, 'pwd', path)
    loaded_key = load_private_key('pwd', path)

    c = encrypt(loaded_key.public_key(), 'text')
    p = decrypt(origin_key, c)
    assert 'text' == p


@test_util.experimental()
def test_what_if_load_private_key_file_with_wrong_password():
    path = from_here(test_util.take_one_unique_test_file_name())
    origin_key = generate_private_key()
    dump_private_key(origin_key, 'pwd', path)
    try:
        loaded_key = load_private_key('wrong_pwd', path)
    except ValueError as e:
        print(e)
