import reactivex as rx

from rules import ConfigParser, loader
from rules.user import User
from rules.user.source_rules import UserSourceRule

loader.import_rule_classes()


class TestUserSourceRuleAnyOfSet:
    class TestUserSourceRule(UserSourceRule):
        _keyword = 'sr'
        num: int

        def __call__(self):
            return rx.of([User(id=i) for i in range(self.num)])

    def test_source_merge_and_distinct(self):
        rule_set = ConfigParser.parse({'any_of': [{'sr': {'num': 1}}, {'sr': {'num': 3}}]},
                                      UserSourceRule)
        for r in rule_set.rules:
            assert isinstance(r, self.TestUserSourceRule)
