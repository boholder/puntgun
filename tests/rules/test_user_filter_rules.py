from rules import ConfigParser
from rules.user.filter_rules import UserFilterRule


def test_follower_user_filter_rule_parsing():
    r = ConfigParser.parse({'follower': {'less_than': 20, 'more_than': 10}}, UserFilterRule)
    assert r(15)
    assert not (r(0) or r(30))


def test_following_user_filter_rule_parsing():
    r = ConfigParser.parse({'following': {'less_than': 20, 'more_than': 10}}, UserFilterRule)
    assert r(15)
    assert not (r(0) or r(30))
