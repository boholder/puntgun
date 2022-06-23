import pytest

from conf.encrypto import generate_private_key, dump_private_key


def experimental(func):
    """Decorator. Skip this test because it's for testing behaviors of libraries etc. for developing."""

    @pytest.mark.skip(reason="experimental")
    def decorator(*args, **kwargs):
        return func(*args, **kwargs)

    return decorator


@pytest.fixture
def generated_key_file(tmp_path):
    file = tmp_path.joinpath('pri_key_file')
    origin_key = generate_private_key()
    dump_private_key(origin_key, 'pwd', file)
    return file, origin_key


@pytest.fixture
def mock_private_key_file(monkeypatch, generated_key_file):
    monkeypatch.setattr('conf.config.pri_key_file_path', generated_key_file[0])
    return generated_key_file
