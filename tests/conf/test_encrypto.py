from io import StringIO
from unittest.mock import Mock

import pytest

from puntgun.conf import encrypto


def test_all_cryptographic_methods(generated_key_file):
    loaded_key = encrypto.load_private_key('pwd', generated_key_file[0])
    c = encrypto.encrypt(loaded_key.public_key(), 'text')
    p = encrypto.decrypt(generated_key_file[1], c)
    assert 'text' == p


def test_load_private_key_file_with_wrong_password(generated_key_file):
    with pytest.raises(ValueError):
        encrypto.load_private_key('wrong_pwd', generated_key_file[0])


def test_load_private_key_file_with_correct_password_interactively(mock_private_key_file, monkeypatch):
    # enter password to load private key
    monkeypatch.setattr('builtins.input', Mock(side_effect=['wrong', 'y', 'wrong again', 'y', 'pwd', 'y']))
    expect = mock_private_key_file[1]
    actual = encrypto.load_or_generate_private_key()
    assert 'text' == encrypto.decrypt(actual, encrypto.encrypt(expect.public_key(), 'text'))


def test_load_private_key_file_from_stdin(mock_private_key_file, monkeypatch, mock_configuration):
    # let the tool read password from stdin
    mock_configuration({'read_password_from_stdin': True})
    # mock stdin to input password
    monkeypatch.setattr('sys.stdin', StringIO('pwd'))
    expect = mock_private_key_file[1]
    actual = encrypto.load_or_generate_private_key()
    assert 'text' == encrypto.decrypt(actual, encrypto.encrypt(expect.public_key(), 'text'))
