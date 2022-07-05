import time
from typing import Optional

import pytest
import reactivex as rx

from client import NeedClient
from rules import ConfigParser, loader
from rules.user import User
from rules.user.filter_rules import UserFilterRule
from rules.user.rule_sets import UserSourceRuleAnyOfSet, UserFilterRuleAllOfSet
from rules.user.source_rules import UserSourceRule


@pytest.fixture(autouse=True)
def load_rule_classes():
    loader.import_rule_classes()


class TestUserSourceRuleAnyOfSet:
    class TUserSourceRule(UserSourceRule):
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
        self.TUserSourceRule(num=2)().subscribe(on_next=user_id_sequence_asserter)

    def test_source_merge_and_distinct(self, user_id_sequence_asserter):
        rule_set = ConfigParser.parse({'any_of': [{'sr': {'num': 1}}, {'sr': {'num': 3}}]},
                                      UserSourceRule)

        # check type
        assert isinstance(rule_set, UserSourceRuleAnyOfSet)
        for r in rule_set.rules:
            assert isinstance(r, self.TUserSourceRule)

        # two test rules result merge into [User(id=0), User(id=1), User(id=2)]
        rule_set().subscribe(on_next=user_id_sequence_asserter)


class TestUserFilterRuleSetBase:
    """Will reuse them multiple times"""

    class TImmediateFilterRule(UserFilterRule):
        _keyword = 'ir'
        will_return: bool

        def __call__(self, user: User):
            return self.will_return

    class TSlowFilterRuleTrue(UserFilterRule, NeedClient):
        _keyword = 'srt'
        will_return: bool
        wait: int
        count: Optional[int] = 0

        def __call__(self, user: User):
            for _ in range(self.wait):
                time.sleep(1)
                self.count += 1
                print('still running')
            return self.will_return


class TestUserFilterRuleAllOfSet(TestUserFilterRuleSetBase):

    @pytest.fixture
    def assert_result(self):
        def factory(expect: bool):
            def real(actual: bool):
                assert actual is expect

            return real

        return factory

    def test_all_rules_are_immediate_rule(self, assert_result):
        rule_set = ConfigParser.parse({'all_of': [{'ir': {'will_return': True}},
                                                  {'ir': {'will_return': False}}]},
                                      UserFilterRule)

        # check type
        assert isinstance(rule_set, UserFilterRuleAllOfSet)
        for r in rule_set.immediate_rules:
            assert isinstance(r, self.TImmediateFilterRule)

        # there are one rule return false so the whole result is false
        rule_set(User()).subscribe(on_next=assert_result(False))

        rule_set.immediate_rules = [self.TImmediateFilterRule(will_return=True)] * 2
        # now it will return true
        rule_set(User()).subscribe(on_next=assert_result(True))

    def test_short_circuit_return_by_immediate_rule(self, assert_result):
        rule_set = ConfigParser.parse({'all_of': [{'ir': {'will_return': False}},
                                                  {'srt': {'wait': 10, 'will_return': True}}]},
                                      UserFilterRule)

        # check type
        assert isinstance(rule_set, UserFilterRuleAllOfSet)
        assert isinstance(rule_set.immediate_rules[0], self.TImmediateFilterRule)
        assert isinstance(rule_set.slow_rules[0], self.TSlowFilterRuleTrue)

        # will not actually execute the slow rule
        rule_set(User()).subscribe(on_next=assert_result(False))

    def test_short_circuit_return_by_slow_rule(self, assert_result):
        rule_set = ConfigParser.parse({'all_of': [{'ir': {'will_return': True}},
                                                  {'srt': {'wait': 1, 'will_return': False}},
                                                  {'srt': {'wait': 3, 'will_return': True}}]},
                                      UserFilterRule)
        # will run two seconds then return the first slow rule's result as final result
        rule_set(User()).subscribe(on_next=assert_result(False))
        assert rule_set.slow_rules[0].count == 1
