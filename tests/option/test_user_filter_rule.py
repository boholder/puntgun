import datetime
from datetime import datetime as dt
from typing import List
from unittest import TestCase

from hamcrest import assert_that, calling, raises, is_

from puntgun.model.context import Context
from puntgun.model.user import User
from puntgun.option.filter_rule import UserCreatedFilterRule, UserTextsMatchFilterRule


class TestUserCreated(TestCase):
    def test_check_time_order(self):
        assert_that(calling(UserCreatedFilterRule)
                    .with_args({'before': '2018-01-01', 'after': '2020-01-01'}),
                    raises(AssertionError, pattern='should be after'))

    def test_convert_when_building(self):
        rule = UserCreatedFilterRule({'before': '2020-01-01', 'after': '2018-01-01 12:00:00'})
        assert_that(rule.before, is_(dt.fromisoformat('2020-01-01 00:00:00')))
        assert_that(rule.after, is_(dt.fromisoformat('2018-01-01 12:00:00')))

    def test_before(self):
        rule = UserCreatedFilterRule({'before': '2018-01-01'})
        assert_that(rule.judge(self.user_create_at('2020-01-01')), is_(False))
        assert_that(rule.judge(self.user_create_at('2015-01-01')), is_(True))

    def test_after(self):
        rule = UserCreatedFilterRule({'after': '2018-01-01'})
        assert_that(rule.judge(self.user_create_at('2020-01-01')), is_(True))
        assert_that(rule.judge(self.user_create_at('2015-01-01')), is_(False))

    def test_before_after(self):
        rule = UserCreatedFilterRule({'after': '2018-01-01 12:30:40', 'before': '2020-01-01 12:30:50'})
        # edge cases are True
        assert_that(rule.judge(self.user_create_at('2020-01-01 12:30:40')), is_(True))
        assert_that(rule.judge(self.user_create_at('2018-01-01 12:30:50')), is_(True))
        # a normal one
        assert_that(rule.judge(self.user_create_at('2019-01-01 00:00:00')), is_(True))

    def test_within_days(self):
        rule = UserCreatedFilterRule({'within_days': 10})
        now = dt.utcnow()
        assert_that(rule.judge(Context(User(created_at=now - datetime.timedelta(days=5)))), is_(True))
        assert_that(rule.judge(Context(User(created_at=now - datetime.timedelta(days=20)))), is_(False))

    @staticmethod
    def user_create_at(time: str):
        return Context(User(created_at=dt.fromisoformat(time)))


class TestUserTextsMatchFilterRule(TestCase):
    import yaml

    def test_simple_match(self):
        self.run_assert('a', 'abc', True)

    def test_simple_not_match(self):
        self.run_assert('abc', 'def', False)

    def test_yaml_escape(self):
        # it seems that this yaml library doesn't care about quoting for escaping : and -
        self.run_assert('a:b-', 'a:b-', True)
        self.run_assert("'a:b-'", 'a:b-', True)
        self.run_assert('"a:b-"', 'a:b-', True)

    def test_python_regex_escape(self):
        # python regex escape
        self.run_assert(r'\d+', '123', True)
        # quote for escaping : and -, while using python regex escape
        self.run_assert(r'"\\d+:-"', '123:-', True)
        # single backslash
        self.run_assert(r'a\\b', 'a' + chr(92) + 'b', True)
        # single backslash without quote
        self.run_assert('a\\b', 'a' + chr(92) + 'b', True)
        # single backslash with quote
        self.run_assert("'a\\\\b'", 'a' + chr(92) + 'b', True)
        self.run_assert('"a\\\\b"', 'a' + chr(92) + 'b', True)

    def run_assert(self, regex: str, text: str, expected: bool):
        rule = UserTextsMatchFilterRule.build(self.get_yaml_parsed(regex))
        texts = [text, '', '']
        for _ in range(3):
            # rotate valid text to different position to represent different user text
            texts = texts[1:] + [texts[0]]
            assert_that(rule.judge(self.user_texts_are(texts)), is_(expected))

    def get_yaml_parsed(self, regex: str):
        return self.yaml.safe_load('regex: ' + regex).get('regex')

    @staticmethod
    def user_texts_are(texts: List[str]):
        words = [t if t else '' for t in texts[0:3]]
        return Context(User(name=words[0], description=words[1], pinned_tweet_text=words[2]))
