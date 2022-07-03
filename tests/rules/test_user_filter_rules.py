from rules import ConfigParser
from rules.user import User
from rules.user.filter_rules import UserFilterRule


def test_follower_user_filter_rule_parsing():
    r = ConfigParser.parse({'follower': {'less_than': 20, 'more_than': 10}}, UserFilterRule)
    assert r(User(followers_count=15))
    assert not (r(User(followers_count=0)) or r(User(followers_count=30)))


def test_following_user_filter_rule_parsing():
    r = ConfigParser.parse({'following': {'less_than': 20, 'more_than': 10}}, UserFilterRule)
    assert r(User(following_count=15))
    assert not (r(User(following_count=0)) or r(User(following_count=30)))
