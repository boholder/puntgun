"""For speed up testing, multiple test cases are compressed into one case."""
from io import StringIO

import pytest

from puntgun.conf import encrypto


def test_all_cryptographic_methods(generated_key_file):
    # load private key with wrong password
    with pytest.raises(ValueError):
        encrypto.load_private_key("wrong_pwd", generated_key_file[0])

    # load with correct password
    loaded_key = encrypto.load_private_key("pwd", generated_key_file[0])

    c = encrypto.encrypt(loaded_key.public_key(), "text")
    p = encrypto.decrypt(generated_key_file[1], c)
    assert "text" == p


def test_load_or_generate_private_key_file(mock_private_key_file, mock_configuration, monkeypatch, mock_input,
                                           tmp_path):
    # 1. load private key file with correct password interactively
    # enter password to load private key
    mock_input("wrong password", "y", "wrong again", "y", "wrong again", "y", "pwd", "y")
    actual_key_input = encrypto.load_or_generate_private_key()

    # 2. load private key file with password from stdin
    # let the tool read password from stdin
    mock_configuration({"read_password_from_stdin": True})
    # mock input password from stdin
    monkeypatch.setattr("sys.stdin", StringIO("pwd"))
    actual_key_stdin = encrypto.load_or_generate_private_key()

    # 3. generate private key if private key file not exists
    mock_private_key = mock_private_key_file[1]
    # mock encrypto module's private key generating function
    monkeypatch.setattr("puntgun.conf.encrypto.generate_private_key", lambda: mock_private_key)
    # remove previous mocked private key file for triggering generating if branch
    monkeypatch.setattr("puntgun.conf.config.pri_key_file", tmp_path.joinpath("new_pri_file"))
    # remove configuration
    mock_configuration({"read_password_from_stdin": False})

    # do generate, will require entering a password
    mock_input("new_pwd", "y")
    encrypto.load_or_generate_private_key()
    # get the private key from newly dumped file, use the new password
    mock_input("new_pwd", "y")
    actual_key_generated = encrypto.load_or_generate_private_key()

    # now test all three branches results
    encrypt_text = encrypto.encrypt(mock_private_key.public_key(), "text")
    assert (
            "text"
            == encrypto.decrypt(actual_key_input, encrypt_text)
            == encrypto.decrypt(actual_key_stdin, encrypt_text)
            == encrypto.decrypt(actual_key_generated, encrypt_text)
    )
