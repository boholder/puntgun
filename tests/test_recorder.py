import datetime

import pytest
from hamcrest import assert_that, all_of, contains_string

from recorder import Record

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
        assert_that(Record(name='user', data={'a': {'b': 123}, 'd': ['e', 'f']}).to_json(),
                    all_of(contains_string('"type": "user",'),
                           contains_string(f'"time": "{MOCK_TIME_NOW.isoformat()}",'),
                           contains_string('"data": {'),
                           contains_string('"a": {'),
                           contains_string('"b": 123'),
                           contains_string('"d": ['),
                           contains_string('"e"'),
                           contains_string('"f"')))

    def test_parse_from_dict(self):
        actual = Record.from_parsed_dict({'type': 'user', 'data': {'a': {'b': 123}, 'd': ['e', 'f']}})
        expect = Record(name='user', data={'a': {'b': 123}, 'd': ['e', 'f']})
        assert actual.__eq__(expect)
