import datetime

import pytest
from hamcrest import assert_that, all_of, contains_string

from recorder import Record

MOCK_TIME_NOW = datetime.datetime(2022, 1, 1)


class TestRecord:
    @pytest.fixture(autouse=True)
    def patch_datetime_now(self, monkeypatch):
        class MockDatetime:
            @classmethod
            def now(cls):
                """make sure datetime.now() returns same instance for assertion convenience"""
                return MOCK_TIME_NOW

        monkeypatch.setattr('datetime.datetime', MockDatetime)

    def test_to_yaml(self, patch_datetime_now):
        # to yaml string
        yaml = Record(name='user', data={'a': {'b': 'c'}, 'd': ['e', 'f']}).to_yaml()

        # It's hard to indicate exact position (which line) of fields,
        # that's depends on pyyaml's inner logic.
        assert_that(yaml, all_of(contains_string('- data:'),
                                 contains_string('    a:'),
                                 contains_string('b: c'),
                                 contains_string('    d:'),
                                 contains_string('    - e'),
                                 contains_string('    - f'),
                                 contains_string(f'  time: {MOCK_TIME_NOW}'),
                                 contains_string('  type: user')))

    def test_parse_from_yaml(self):
        actual = Record.from_parsed_yaml({'type': 'user', 'data': {'a': {'b': 'c'}, 'd': ['e', 'f']}})
        expect = Record(name='user', data={'a': {'b': 'c'}, 'd': ['e', 'f']})
        assert actual.__eq__(expect)
