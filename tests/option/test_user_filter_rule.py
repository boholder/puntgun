import datetime
from datetime import datetime as dt
from unittest import TestCase

from hamcrest import assert_that, calling, raises, is_

from puntgun.model.context import Context
from puntgun.model.user import User
from puntgun.option.filter_rule import UserCreatedFilterRule


class TestUserCreated(TestCase):
    def test_check_time_order(self):
        assert_that(calling(UserCreatedFilterRule)
                    .with_args({'before': '2018-01-01', 'after': '2020-01-01'}),
                    raises(AssertionError, pattern="should be after"))

    def test_convert_when_building(self):
        rule = UserCreatedFilterRule({'before': '2020-01-01', 'after': '2018-01-01 12:00:00'})
        assert_that(rule.before, is_(dt.fromisoformat('2020-01-01 00:00:00')))
        assert_that(rule.after, is_(dt.fromisoformat('2018-01-01 12:00:00')))

    def test_before(self):
        rule = UserCreatedFilterRule({'before': '2018-01-01'})
        assert_that(rule.judge(Context(User(created_at=dt.fromisoformat('2020-01-01')))), is_(False))
        assert_that(rule.judge(Context(User(created_at=dt.fromisoformat('2015-01-01')))), is_(True))

    def test_after(self):
        rule = UserCreatedFilterRule({'after': '2018-01-01'})
        assert_that(rule.judge(Context(User(created_at=dt.fromisoformat('2020-01-01')))), is_(True))
        assert_that(rule.judge(Context(User(created_at=dt.fromisoformat('2015-01-01')))), is_(False))

    def test_before_after(self):
        rule = UserCreatedFilterRule({'after': '2018-01-01 12:30:40', 'before': '2020-01-01 12:30:50'})
        # edge cases are True
        assert_that(rule.judge(Context(User(created_at=dt.fromisoformat('2020-01-01 12:30:40')))), is_(True))
        assert_that(rule.judge(Context(User(created_at=dt.fromisoformat('2018-01-01 12:30:50')))), is_(True))
        # a normal one
        assert_that(rule.judge(Context(User(created_at=dt.fromisoformat('2019-01-01 00:00:00')))), is_(True))

    def test_within_days(self):
        rule = UserCreatedFilterRule({'within_days': 10})
        now = dt.utcnow()
        assert_that(rule.judge(Context(User(created_at=now - datetime.timedelta(days=5)))), is_(True))
        assert_that(rule.judge(Context(User(created_at=now - datetime.timedelta(days=20)))), is_(False))
