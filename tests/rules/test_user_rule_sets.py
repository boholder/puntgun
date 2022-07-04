import reactivex as rx

from rules import ConfigParser
from rules.user import User
from rules.user.source_rules import UserSourceRule
from rules.user.rule_sets import UserSourceRuleAnyOfSet


class TestUserSourceRuleAnyOfSet:
    class TestUserSourceRule(UserSourceRule):
        _keyword = 'sr'
        num: int

        def __call__(self):
            return rx.of([User(id=i) for i in range(self.num)])

    def test_source_merge_and_distinct(self):
        rule_set = ConfigParser.parse({'any_of': [{'sr': {'num': 1}}, {'sr': {'num': 3}}]},
                                      UserSourceRule)
        print(rule_set)
