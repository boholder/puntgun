from from_root import from_here
from puntgun.conf.secrets import generate_private_key, dump_private_key, load_private_key, encrypt, decrypt


def test_all_private_key_things():
    path = str(from_here('test_pri_key_file').absolute())
    origin_key = generate_private_key()
    dump_private_key(path, origin_key, 'pwd')
    loaded_key = load_private_key(path, 'pwd')

    c = encrypt(loaded_key.public_key(), 'text')
    p = decrypt(origin_key, c)
    assert 'text' == p
