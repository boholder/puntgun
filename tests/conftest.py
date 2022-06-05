import pytest

from puntgun.conf.encrypto import generate_private_key, dump_private_key


def experimental():
    """Decorator. Skip this test because it's for testing behaviors of libraries etc. for developing."""

    def decorator(func):
        @pytest.mark.skip(reason="experimental")
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    return decorator


@pytest.fixture
def generated_key_file(tmp_path):
    file = tmp_path.joinpath('pri_key_file')
    origin_key = generate_private_key()
    dump_private_key(origin_key, 'pwd', file)
    return file, origin_key


@pytest.fixture
def mock_private_key_file(monkeypatch, generated_key_file):
    monkeypatch.setattr('puntgun.conf.config.pri_key_file_path', generated_key_file[0])
    return generated_key_file
