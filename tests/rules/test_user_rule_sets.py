from __future__ import annotations

import time

import pytest
import reactivex as rx
from reactivex import operators as op

from puntgun.client import NeedClientMixin
from puntgun.rules.config_parser import ConfigParser
from puntgun.rules.data import RuleResult, User
from puntgun.rules.user.action_rules import UserActionRule
from puntgun.rules.user.filter_rules import UserFilterRule
from puntgun.rules.user.rule_sets import (
    UserFilterRuleAllOfSet,
    UserFilterRuleAnyOfSet,
    UserSourceRuleResultMergingSet,
    execution_wrapper,
)
from puntgun.rules.user.source_rules import UserSourceRule


class TestUserSourceRuleResultMergingSet:
    class TUserSourceRule(UserSourceRule):
        _keyword = "sr"
        num: int

        def __call__(self):
            return rx.from_iterable([User(id=i) for i in range(self.num)])

    def test_test_rule_function(self, user_id_sequence_checker):
        self.TUserSourceRule(num=2)().pipe(op.do(rx.Observer(on_next=user_id_sequence_checker))).run()
        # make sure the reactivex pipeline really ran
        assert user_id_sequence_checker.call_count == 2

    def test_source_merge_and_distinct(self, user_id_sequence_checker):
        rule_set = ConfigParser.parse({"any_of": [{"sr": {"num": 1}}, {"sr": {"num": 3}}]}, UserSourceRule)

        # check type
        assert isinstance(rule_set, UserSourceRuleResultMergingSet)
        for r in rule_set.rules:
            assert isinstance(r, self.TUserSourceRule)

        # two test rules result merge into [User(id=0), User(id=1), User(id=2)]
        rule_set().pipe(op.do(rx.Observer(on_next=user_id_sequence_checker))).run()
        assert user_id_sequence_checker.call_count == 3

    def test_merge_on_single_source_rule(self, user_id_sequence_checker):
        rule_set = ConfigParser.parse({"any_of": [{"sr": {"num": 2}}]}, UserSourceRule)

        # check type
        assert isinstance(rule_set, UserSourceRuleResultMergingSet)
        for r in rule_set.rules:
            assert isinstance(r, self.TUserSourceRule)
        # two elements in pipeline: [User(id=0), User(id=1)]
        rule_set().pipe(op.do(rx.Observer(on_next=user_id_sequence_checker))).run()
        assert user_id_sequence_checker.call_count == 2


class TImmediateFilterRule(UserFilterRule):
    _keyword = "ir"
    will_return: bool

    def __call__(self, user: User):
        return self.will_return


class TSlowFilterRuleTrue(UserFilterRule, NeedClientMixin):
    _keyword = "srt"
    will_return: bool
    wait: int
    work_count: int | None = 0

    def __call__(self, user: User):
        for _ in range(self.wait):
            time.sleep(0.1)
            # proof that the slow rule is still running
            self.work_count += 1
        return rx.just(self.will_return)


@pytest.fixture
def filter_rule_result_checker():
    """For user filter rule sets testing."""

    def factory(expect: bool):
        factory.call_count = 0

        def real(actual):
            factory.call_count += 1
            assert bool(actual) is expect

        return real

    return factory


class TestUserFilterRuleAllOfSet:
    def test_all_rules_are_immediate_rule(self, filter_rule_result_checker):
        rule_set = ConfigParser.parse(
            {"all_of": [{"ir": {"will_return": True}}, {"ir": {"will_return": False}}]}, UserFilterRule
        )

        # there are one rule return false so the whole result is false
        rule_set(User()).subscribe(on_next=filter_rule_result_checker(False))
        assert filter_rule_result_checker.call_count == 1

        # change all rules that rule set contains to return true
        rule_set.immediate_rules = [TImmediateFilterRule(will_return=True)] * 2
        # now it will return true
        rule_set(User()).subscribe(on_next=filter_rule_result_checker(True))
        assert filter_rule_result_checker.call_count == 1

    def test_short_circuit_return_by_immediate_rule(self, filter_rule_result_checker):
        rule_set = ConfigParser.parse(
            {"all_of": [{"ir": {"will_return": False}}, {"srt": {"wait": 10, "will_return": True}}]}, UserFilterRule
        )

        # check type
        assert isinstance(rule_set, UserFilterRuleAllOfSet)
        assert isinstance(rule_set.immediate_rules[0], TImmediateFilterRule)
        assert isinstance(rule_set.slow_rules[0], TSlowFilterRuleTrue)

        # will not actually execute the slow rule
        rule_set(User()).subscribe(on_next=filter_rule_result_checker(False))
        assert filter_rule_result_checker.call_count == 1

    def test_rule_execution_wrapper(self):
        rule_wrapper = execution_wrapper(User(), TImmediateFilterRule(will_return=True))
        assert rule_wrapper() is True

    def test_short_circuit_return_by_slow_rule(self, filter_rule_result_checker):
        rule_set = ConfigParser.parse(
            {
                "all_of": [
                    {"ir": {"will_return": True}},
                    {"srt": {"wait": 1, "will_return": False}},
                    {"srt": {"wait": 10000, "will_return": True}},
                ]
            },
            UserFilterRule,
        )
        # will return the first slow rule's result (False) as final result
        rule_set(User()).pipe(op.do(rx.Observer(on_next=filter_rule_result_checker(False)))).run()
        assert rule_set.slow_rules[0].work_count == 1
        # this slow rule won't finish its work
        assert rule_set.slow_rules[1].work_count < 10000

    def test_lone_return_by_slow_rule(self, filter_rule_result_checker):
        rule_set = ConfigParser.parse(
            {
                "all_of": [
                    {"ir": {"will_return": True}},
                    {"srt": {"wait": 1, "will_return": True}},
                    {"srt": {"wait": 1, "will_return": True}},
                ]
            },
            UserFilterRule,
        )
        # will finally return True after all slow rules are finished
        rule_set(User()).pipe(op.do(rx.Observer(on_next=filter_rule_result_checker(True)))).run()
        assert rule_set.slow_rules[0].work_count == 1
        assert rule_set.slow_rules[1].work_count == 1


class TestUserFilterRuleAnyOfSet:
    """Mainly copy cases in the TestUserFilterRuleAllOfSet"""

    def test_all_rules_are_immediate_rule(self, filter_rule_result_checker):
        rule_set = ConfigParser.parse(
            {"any_of": [{"ir": {"will_return": True}}, {"ir": {"will_return": False}}]}, UserFilterRule
        )

        # rule_set(User()).subscribe(on_next=filter_rule_result_checker(True))
        # assert filter_rule_result_checker.call_count == 1

        rule_set.immediate_rules = [TImmediateFilterRule(will_return=False)] * 2
        rule_set(User()).subscribe(on_next=filter_rule_result_checker(False))
        assert filter_rule_result_checker.call_count == 1

    def test_short_circuit_return_by_immediate_rule(self, filter_rule_result_checker):
        rule_set = ConfigParser.parse(
            {"any_of": [{"ir": {"will_return": True}}, {"srt": {"wait": 10000, "will_return": False}}]}, UserFilterRule
        )

        assert isinstance(rule_set, UserFilterRuleAnyOfSet)
        assert isinstance(rule_set.immediate_rules[0], TImmediateFilterRule)
        assert isinstance(rule_set.slow_rules[0], TSlowFilterRuleTrue)

        rule_set(User()).subscribe(on_next=filter_rule_result_checker(True))
        assert filter_rule_result_checker.call_count == 1

    def test_short_circuit_return_by_slow_rule(self, filter_rule_result_checker):
        rule_set = ConfigParser.parse(
            {
                "any_of": [
                    {"ir": {"will_return": False}},
                    {"srt": {"wait": 1, "will_return": True}},
                    {"srt": {"wait": 10000, "will_return": False}},
                ]
            },
            UserFilterRule,
        )

        rule_set(User()).pipe(op.do(rx.Observer(on_next=filter_rule_result_checker(True)))).run()
        assert rule_set.slow_rules[0].work_count == 1
        assert rule_set.slow_rules[1].work_count < 10000

    def test_lone_return_by_slow_rule(self, filter_rule_result_checker):
        rule_set = ConfigParser.parse(
            {
                "any_of": [
                    {"ir": {"will_return": False}},
                    {"srt": {"wait": 1, "will_return": False}},
                    {"srt": {"wait": 1, "will_return": False}},
                ]
            },
            UserFilterRule,
        )
        rule_set(User()).pipe(op.do(rx.Observer(on_next=filter_rule_result_checker(False)))).run()
        assert rule_set.slow_rules[0].work_count == 1
        assert rule_set.slow_rules[1].work_count == 1

    def test_rule_set_nesting(self, filter_rule_result_checker):
        rule_set = ConfigParser.parse(
            {"all_of": [{"all_of": [{"ir": {"will_return": True}}]}, {"all_of": [{"ir": {"will_return": True}}]}]},
            UserFilterRule,
        )

        # type is right
        for inner in rule_set.slow_rules:
            assert isinstance(inner, UserFilterRuleAllOfSet)

        # can function normally
        rule_set(User()).pipe(op.do(rx.Observer(on_next=filter_rule_result_checker(True)))).run()
        assert filter_rule_result_checker.call_count == 1


class TUserActionRule(UserActionRule):
    _keyword = "tuar"

    will_return: bool

    def __call__(self, user: User):
        return RuleResult(self, self.will_return)


class TestUserActionRuleResultCollectingSet:
    def test_result_aggregating(self):
        def action_ruleset_result_checker(results: list[RuleResult]):
            """For user filter rule sets testing."""
            action_ruleset_result_checker.call_count = 0

            for r in results:
                assert isinstance(r.rule, TUserActionRule)
                action_ruleset_result_checker.call_count += 1

            assert bool(results[0]) is True
            assert bool(results[1]) is False

        rule_set = ConfigParser.parse(
            {"all_of": [{"tuar": {"will_return": True}}, {"tuar": {"will_return": False}}]}, UserActionRule
        )

        for rule in rule_set.rules:
            assert isinstance(rule, TUserActionRule)

        rule_set(User()).pipe(op.do(rx.Observer(on_next=action_ruleset_result_checker))).run()
        assert action_ruleset_result_checker.call_count == 2
