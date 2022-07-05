import pytest
import reactivex as rx

from rules import ConfigParser, loader
from rules.user import User
from rules.user.rule_sets import UserSourceRuleAnyOfSet
from rules.user.source_rules import UserSourceRule

# import rule classes first
loader.import_rule_classes()


class TestUserSourceRuleAnyOfSet:
    class TestUserSourceRule(UserSourceRule):
        _keyword = 'sr'
        num: int

        def __call__(self):
            return rx.from_iterable([User(id=i) for i in range(self.num)])

    @pytest.fixture
    def user_id_sequence_asserter(self):
        id_count = 0

        def check_result(u: User):
            nonlocal id_count
            assert u.id == id_count
            id_count += 1

        return check_result

    def test_test_rule_function(self, user_id_sequence_asserter):
        self.TestUserSourceRule(num=2)().subscribe(on_next=user_id_sequence_asserter)

    def test_source_merge_and_distinct(self, user_id_sequence_asserter):
        rule_set = ConfigParser.parse({'any_of': [{'sr': {'num': 1}}, {'sr': {'num': 3}}]},
                                      UserSourceRule)

        # check type
        assert isinstance(rule_set, UserSourceRuleAnyOfSet)
        for r in rule_set.rules:
            assert isinstance(r, self.TestUserSourceRule)

        # two test rules result merge into [User(id=0), User(id=1), User(id=2)]
        rule_set().subscribe(on_next=user_id_sequence_asserter)
