from unittest.mock import MagicMock

import pytest

import client
from conf.encrypto import generate_private_key, dump_private_key
from rules.config_parser import ConfigParser


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


@pytest.fixture
def mock_client(monkeypatch):
    c = MagicMock()
    # set client field for each rule to mock_client
    monkeypatch.setattr(client.Client, 'singleton', lambda: c)
    return c


@pytest.fixture
def user_id_sequence_checker():
    """
    For user source rules testing.
    Check if the reactivex pipeline is producing User(id=0), User(id=1), User(id=2), ...

    How we know if the reactive pipeline really run when running test cases?
    It is just running silently, if it actually doesn't run, you won't fail the test,
    but we need to fail the test in this case.

    Here is the solution:
    1. Make a mock.Mock() like consumer function (this function) which record invocation count.
    2. Run the reactivex pipeline with
       Observable.pipe(op.do(rx.Observer(on_next=...))).run()
       the Observable.run() will synchronously start and finish the pipeline.
    3. After the pipeline ran, we verify the invocation count should not be zero.
    """
    call_count = 0

    def check_result(u):
        nonlocal call_count
        # check user's id
        assert u.id == call_count
        call_count += 1

        # let test cases to verify the consumer is really running
        check_result.call_count = call_count

    return check_result


@pytest.fixture
def clean_config_parser():
    ConfigParser.clear_errors()
