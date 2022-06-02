import datetime
from datetime import datetime as dt
from typing import List
from unittest import TestCase

from hamcrest import assert_that, calling, raises, is_

from puntgun.old.model import Context
from puntgun.old.model import User
from puntgun.old.option.filter_rule import UserCreatedFilterRule, UserTextsMatchFilterRule, UserCreatedAfterFilterRule, \
    UserCreatedWithinDaysFilterRule, IntComparingFilterRule, UserFollowerFilterRule, UserFollowerLessThanFilterRule, \
    UserFollowingMoreThanFilterRule, UserFollowingFilterRule, FloatComparingFilterRule


class TestUserCreatedFilterRule(TestCase):
    def test_check_time_order(self):
        assert_that(calling(UserCreatedFilterRule.build).with_args({'before': '2018-01-01', 'after': '2020-01-01'}),
                    raises(AssertionError, pattern='should be after'))

    def test_convert_when_building(self):
        rule = UserCreatedFilterRule.build({'before': '2020-01-01', 'after': '2018-01-01 12:00:00'})
        assert_that(rule.before, is_(dt.fromisoformat('2020-01-01 00:00:00')))
        assert_that(rule.after, is_(dt.fromisoformat('2018-01-01 12:00:00')))

    def test_before(self):
        rule = UserCreatedFilterRule.build({'before': '2018-01-01'})
        assert_that(rule.judge(self.user_create_at('2020-01-01')), is_(False))
        assert_that(rule.judge(self.user_create_at('2015-01-01')), is_(True))

    def test_after(self):
        self.assert_after(UserCreatedFilterRule.build({'after': '2018-01-01'}))

    def test_shorten_after(self):
        self.assert_after(UserCreatedAfterFilterRule.build('2018-01-01'))

    def assert_after(self, rule):
        assert_that(rule.judge(self.user_create_at('2020-01-01')), is_(True))
        assert_that(rule.judge(self.user_create_at('2015-01-01')), is_(False))

    def test_before_after(self):
        rule = UserCreatedFilterRule.build({'after': '2018-01-01 12:30:40', 'before': '2020-01-01 12:30:50'})
        # edge cases are True
        assert_that(rule.judge(self.user_create_at('2020-01-01 12:30:40')), is_(True))
        assert_that(rule.judge(self.user_create_at('2018-01-01 12:30:50')), is_(True))
        # a normal one
        assert_that(rule.judge(self.user_create_at('2019-01-01 00:00:00')), is_(True))

    def test_within_days(self):
        self.assert_within_days(UserCreatedFilterRule.build({'within_days': 10}))

    def test_shorten_within_days(self):
        self.assert_within_days(UserCreatedWithinDaysFilterRule.build(10))

    @staticmethod
    def assert_within_days(rule):
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


class IntComparingFilterRuleTestCase(TestCase):
    def setUp(self) -> None:
        self.build_func = lambda config: IntComparingFilterRule.build(config)
        self.judge_func = lambda rule, num: rule.judge_number(num)
        # convert number type for passing rule option value type check
        self.num = lambda x: x

    def test_check_number_order(self):
        assert_that(calling(self.build_func).with_args({'less_than': self.num(10), 'more_than': self.num(20)}),
                    raises(AssertionError, pattern='should be bigger than'))

    def test_less_than(self):
        rule = self.build_func({'less_than': self.num(10)})
        assert_that(self.judge_func(rule, self.num(5)), is_(True))
        assert_that(self.judge_func(rule, self.num(20)), is_(False))

    def test_more_than(self):
        rule = self.build_func({'more_than': self.num(10)})
        assert_that(self.judge_func(rule, self.num(20)), is_(True))
        assert_that(self.judge_func(rule, self.num(5)), is_(False))

    def test_less_more(self):
        rule = self.build_func({'less_than': self.num(20), 'more_than': self.num(10)})
        assert_that(self.judge_func(rule, self.num(15)), is_(True))
        assert_that(self.judge_func(rule, self.num(5)), is_(False))
        assert_that(self.judge_func(rule, self.num(25)), is_(False))
        # edge case (equal) result in False.
        assert_that(self.judge_func(rule, self.num(10)), is_(False))
        assert_that(self.judge_func(rule, self.num(20)), is_(False))


class TestUserFollowerFilterRule(IntComparingFilterRuleTestCase):
    def setUp(self) -> None:
        self.build_func = lambda config: UserFollowerFilterRule.build(config)
        self.judge_func = lambda rule, num: rule.judge(Context(User(followers_count=num)))

    def test_shorten_less_than(self):
        rule = UserFollowerLessThanFilterRule.build(10)
        assert_that(self.judge_func(rule, 5), is_(True))
        assert_that(self.judge_func(rule, 20), is_(False))


class TestUserFollowingFilterRule(IntComparingFilterRuleTestCase):
    def setUp(self) -> None:
        self.build_func = lambda config: UserFollowingFilterRule.build(config)
        self.judge_func = lambda rule, num: rule.judge(Context(User(following_count=num)))

    def test_shorten_more_than(self):
        rule = UserFollowingMoreThanFilterRule.build(10)
        assert_that(self.judge_func(rule, 20), is_(True))
        assert_that(self.judge_func(rule, 5), is_(False))


class FloatComparingFilterRuleTestCase(IntComparingFilterRuleTestCase):
    def setUp(self) -> None:
        self.build_func = lambda config: FloatComparingFilterRule.build(config)
        self.judge_func = lambda rule, num: rule.judge_number(num)
        self.num = lambda x: float(x)
