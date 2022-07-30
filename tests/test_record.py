import datetime
import re

import loguru
import orjson
import pytest

from record import Record, Recorder, Recordable, load_report
from rules import Plan


class TestRecord:
    def test_to_json(self):
        actual = Record(name='user', data={'a': {'b': 123}, 'd': ['e', 'f']}).to_json().decode('utf-8')
        expect = '{"type":"user","data":{"a":{"b":123},"d":["e","f"]}}'
        assert actual == expect

    def test_parse_from_dict(self):
        actual = Record.parse_from_dict({'type': 'user', 'data': {'a': {'b': 123}, 'd': ['e', 'f']}})
        expect = Record(name='user', data={'a': {'b': 123}, 'd': ['e', 'f']})
        assert actual.__eq__(expect)


class MockLogger:
    """Simulate logger and save logs as one string."""

    def __init__(self):
        self.content = ''

    def bind(self, **kwargs):
        return self

    def info(self, msg: str):
        self.content += msg

    def get_content(self):
        # remove white characters
        return re.sub(r'\s', '', self.content)


@pytest.fixture
def mock_logger(monkeypatch):
    logger = MockLogger()
    monkeypatch.setattr('record.logger', logger)
    return logger


MOCK_TIME_NOW = datetime.datetime(2022, 1, 1)


@pytest.fixture
def mock_datetime_now(monkeypatch):
    class MockDatetime:
        @classmethod
        def now(cls):
            """make sure datetime.now() returns same instance for assertion convenience"""
            return MOCK_TIME_NOW

    monkeypatch.setattr('record.datetime', MockDatetime)


class TPlan(Plan):
    pass


class TRecordable(Recordable):

    def to_record(self) -> Record:
        return Record(name='tr', data={'a': 'b'})

    @staticmethod
    def parse_from_record(record: Record):
        pass


class TestRecorder:
    """These test cases are tightly linked to the implementation."""

    def test_load_report_correct_format(self):
        self.assert_report_load_result('{"records":[{},{"name":"p"},{}]}')

    def test_load_report_no_report_tail(self):
        self.assert_report_load_result('{"records":[{},{"name":"p"},')

    @staticmethod
    def assert_report_load_result(report_content: str):
        expect = {'records': [{'name': 'p'}]}
        actual = load_report(report_content.encode('utf-8'))
        assert actual == expect

    def test_load_report_fail(self):
        with pytest.raises(ValueError) as _:
            load_report('{'.encode('utf-8'))

    def test_write_report_head_tail(self, mock_datetime_now, mock_logger, monkeypatch):
        mock_config_settings = {'plans': [{'p': 123}]}
        monkeypatch.setattr('record.config.settings', mock_config_settings)

        Recorder.write_report_header([TPlan(name='a'), TPlan(name='b')])
        Recorder.write_report_tail()

        actual = orjson.loads(mock_logger.get_content())

        assert actual['generate_time'] == MOCK_TIME_NOW.isoformat()
        assert actual['plan_configuration'] == [{'p': 123}]
        assert actual['plan_ids'] == [{'name': 'a', 'id': 0}, {'name': 'b', 'id': 1}]
        assert actual['records'] == [{}, {}]

    def test_write_multiple_records(self, mock_logger):
        Recorder.write_report_header([])
        Recorder.record(TRecordable())
        Recorder.record(TRecordable())
        Recorder.write_report_tail()

        actual = load_report(mock_logger.get_content().encode('utf-8'))

        assert actual['records'] == [{'type': 'tr', 'data': {'a': 'b'}}] * 2

    @pytest.mark.skip('will generate the report json file')
    def test_real_output(self):
        loguru.logger.add('record.json', format='{message}')
        Recorder.write_report_header([])
        Recorder.record(TRecordable())
        Recorder.record(TRecordable())
        Recorder.write_report_tail()
