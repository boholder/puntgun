from unittest.mock import Mock

import pytest

from conf.encrypto import load_private_key, encrypt, decrypt, \
    load_or_generate_private_key


def test_all_cryptographic_methods(generated_key_file):
    loaded_key = load_private_key('pwd', generated_key_file[0])
    c = encrypt(loaded_key.public_key(), 'text')
    p = decrypt(generated_key_file[1], c)
    assert 'text' == p


def test_load_private_key_file_with_wrong_password(generated_key_file):
    with pytest.raises(ValueError):
        load_private_key('wrong_pwd', generated_key_file[0])


def test_load_private_key_file_with_correct_password_interactively(mock_private_key_file, monkeypatch):
    # enter password to load private key
    monkeypatch.setattr('builtins.input', Mock(side_effect=['wrong', 'y', 'wrong again', 'y', 'pwd', 'y']))
    expect = mock_private_key_file[1]
    actual = load_or_generate_private_key()
    assert 'text' == decrypt(actual, encrypt(expect.public_key(), 'text'))
