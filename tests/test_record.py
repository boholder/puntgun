import datetime

import pytest

from record import Record

MOCK_TIME_NOW = datetime.datetime(2022, 1, 1)


@pytest.fixture(autouse=True)
def mock_datetime_now(monkeypatch):
    class MockDatetime:
        @classmethod
        def now(cls):
            """make sure datetime.now() returns same instance for assertion convenience"""
            return MOCK_TIME_NOW

    monkeypatch.setattr('datetime.datetime', MockDatetime)


class TestRecord:
    def test_to_json(self, mock_datetime_now):
        actual = Record(name='user', data={'a': {'b': 123}, 'd': ['e', 'f']}).to_json()
        expect = '{"type":"user","time":"2022-01-01T00:00:00","data":{"a":{"b":123},"d":["e","f"]}}'
        assert actual == expect

    def test_parse_from_dict(self):
        actual = Record.from_parsed_dict({'type': 'user', 'data': {'a': {'b': 123}, 'd': ['e', 'f']}})
        expect = Record(name='user', data={'a': {'b': 123}, 'd': ['e', 'f']})
        assert actual.__eq__(expect)


class TestRecorder:
    pass
