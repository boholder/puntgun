import re
from unittest.mock import MagicMock, Mock

import pytest

from puntgun.conf import encrypto
from puntgun.rules.config_parser import ConfigParser


@pytest.fixture
def generated_key_file(tmp_path):
    file = tmp_path.joinpath("pri_key_file")
    origin_key = encrypto.generate_private_key()
    encrypto.dump_private_key(origin_key, "pwd", file)
    return file, origin_key


@pytest.fixture
def mock_private_key_file(monkeypatch, generated_key_file):
    monkeypatch.setattr("puntgun.conf.config.pri_key_file", generated_key_file[0])
    return generated_key_file


@pytest.fixture
def mock_client(monkeypatch):
    c = MagicMock()
    # set client field for each rule to mock_client
    monkeypatch.setattr("puntgun.client.Client.singleton", lambda: c)
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
def clean_config_parser_errors():
    """
    Add this on test cases that may cause config parsing errors,
    for avoiding accidentally fail other innocent test cases.
    """
    # clean before the test case
    ConfigParser.clear_errors()
    # https://docs.pytest.org/en/6.2.x/fixture.html#yield-fixtures-recommended
    yield
    # clean after the test case
    ConfigParser.clear_errors()


@pytest.fixture
def mock_configuration(monkeypatch):
    def set_config(new):
        monkeypatch.setattr("puntgun.conf.config.settings", new)

    return set_config


class MockLogger:
    """Simulate logger and save logs as one string."""

    def __init__(self):
        self.content = ""

    def bind(self, **kwargs):
        return self

    def info(self, msg: str):
        self.content += msg

    def get_content(self):
        # remove white characters
        return re.sub(r"\s", "", self.content)


@pytest.fixture
def mock_record_logger(monkeypatch):
    """For getting json format output for assertion."""
    logger = MockLogger()
    monkeypatch.setattr("puntgun.record.logger", logger)
    return logger


@pytest.fixture
def mock_input(monkeypatch):
    def wrapper(*side_effect):
        # return values in sequence when is called multiple times
        mock_func = Mock(side_effect=side_effect)
        monkeypatch.setattr("builtins.input", mock_func)
        monkeypatch.setattr("getpass.getpass", mock_func)

    return wrapper
