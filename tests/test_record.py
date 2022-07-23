import datetime
import re

import orjson
import pytest

from record import Record, Recorder

MOCK_TIME_NOW = datetime.datetime(2022, 1, 1)


@pytest.fixture(autouse=True)
def mock_datetime_now(monkeypatch):
    class MockDatetime:
        @classmethod
        def now(cls):
            """make sure datetime.now() returns same instance for assertion convenience"""
            return MOCK_TIME_NOW

    monkeypatch.setattr('record.datetime', MockDatetime)


class TestRecord:
    def test_to_json(self, mock_datetime_now):
        actual = Record(name='user', data={'a': {'b': 123}, 'd': ['e', 'f']}).to_json().decode('utf-8')
        expect = '{"type":"user","time":"2022-01-01T00:00:00","data":{"a":{"b":123},"d":["e","f"]}}'
        assert actual == expect

    def test_parse_from_dict(self):
        actual = Record.from_parsed_dict({'type': 'user', 'data': {'a': {'b': 123}, 'd': ['e', 'f']}})
        expect = Record(name='user', data={'a': {'b': 123}, 'd': ['e', 'f']})
        assert actual.__eq__(expect)


class MockLogger:
    """Simulate logger and save logs as one string."""

    def __init__(self):
        self.content = ''

    def info(self, msg: bytes):
        self.content += msg.decode('utf-8')

    def get_content(self):
        # remove white characters
        return re.sub(r'\s', '', self.content)


@pytest.fixture
def mock_logger(monkeypatch):
    logger = MockLogger()
    monkeypatch.setattr('record.logger', logger)
    return logger


class TestRecorder:
    """These test cases are tightly linked to the implementation."""

    def test_load_report_correct_format(self):
        self.assert_report_load_result('{"plans":[{},{"name":"p","records":[{},{"r":1},{}]},{}]}')

    def test_load_report_no_report_tail(self):
        self.assert_report_load_result('{"plans":[{},{"name":"p","records":[{},{"r":1},{}]},')

    def test_load_report_no_plan_tail_no_report_tail(self):
        self.assert_report_load_result('{"plans":[{},{"name":"p","records":[{},{"r":1},')

    @staticmethod
    def assert_report_load_result(report_content: str):
        expect = {'plans': [{'name': 'p', 'records': [{'r': 1}]}]}
        actual = Recorder.load_report(report_content.encode('utf-8'))
        assert actual == expect

    def test_load_report_fail(self):
        with pytest.raises(ValueError) as _:
            Recorder.load_report('{'.encode('utf-8'))

    def test_write_report_head_tail(self, mock_logger):
        Recorder.write_report_header()
        Recorder.write_report_tail()
        assert orjson.loads(mock_logger.get_content())['plans'] == [{}, {}]

    def test_write_report_and_plan_head_tail(self, mock_logger):
        pass

    def test(self):
        # TODO 试一下
        pass
