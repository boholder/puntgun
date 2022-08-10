"""
Some user filter rules have simular functions and contain same delegating agents inside them,
"follower rule" and "following rule" for example.
Most functions of these rules are tested when testing delegating agents,
so only basic "parsing" logic will be tested in this test module.
"""
from rules.config_parser import ConfigParser
from rules.user import User
from rules.user.filter_rules import UserFilterRule


def test_follower_user_filter_rule():
    r = ConfigParser.parse({'follower': {'less_than': 20, 'more_than': 10}}, UserFilterRule)
    assert r(User(followers_count=15))
    assert not (r(User(followers_count=0)) or r(User(followers_count=30)))


def test_follower_less_than_filter_rule():
    r = ConfigParser.parse({'follower_less_than': 10}, UserFilterRule)
    assert r(User(followers_count=5))
    assert not r(User(followers_count=20))


def test_following_user_filter_rule():
    r = ConfigParser.parse({'following': {'less_than': 20, 'more_than': 10}}, UserFilterRule)
    assert r(User(following_count=15))
    assert not (r(User(following_count=0)) or r(User(following_count=30)))


def test_following_more_than_filter_rule():
    r = ConfigParser.parse({'following_more_than': 10}, UserFilterRule)
    assert r(User(following_count=20))
    assert not r(User(following_count=5))
