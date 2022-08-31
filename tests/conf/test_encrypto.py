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


def test_load_private_key_file(mock_private_key_file, mock_configuration, monkeypatch, mock_input):
    # load private key file with correct password interactively
    # enter password to load private key
    mock_input("wrong password", "y", "wrong again", "y", "pwd", "y")
    actual_key_input = encrypto.load_or_generate_private_key()

    # load private key file with password from stdin
    # let the tool read password from stdin
    mock_configuration({"read_password_from_stdin": True})
    # mock input password from stdin
    monkeypatch.setattr("sys.stdin", StringIO("pwd"))
    actual_key_stdin = encrypto.load_or_generate_private_key()

    expect = mock_private_key_file[1]
    assert (
        "text"
        == encrypto.decrypt(actual_key_input, encrypto.encrypt(expect.public_key(), "text"))
        == encrypto.decrypt(actual_key_stdin, encrypto.encrypt(expect.public_key(), "text"))
    )
