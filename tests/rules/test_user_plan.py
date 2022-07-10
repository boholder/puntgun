import pytest
import reactivex as rx
from hamcrest import assert_that, contains_string, all_of
from reactivex import operators as op

from rules import Plan
from rules.config_parser import ConfigParser
from rules.user import User
from rules.user.filter_rules import UserFilterRule
from rules.user.rule_sets import UserSourceRuleAnyOfSet, UserFilterRuleAnyOfSet
from rules.user.source_rules import UserSourceRule


class TUserSourceRule(UserSourceRule):
    # DO NOT make the keyword same as any other test rules.
    # Or it may fail test cases that are checking instances type,
    # because the :class:`ConfigParser` may wrongly choose
    # not-in-this-file test rules with same keyword.
    _keyword = 'psr'
    num: int

    def __call__(self):
        return rx.from_iterable([User(id=i) for i in range(self.num)])


class TEvenTrueUserFilterRule(UserFilterRule):
    _keyword = "otf"

    def __call__(self, user: User):
        return user.id % 2 == 0


@pytest.fixture
def even_true_zipped_result_checker():
    """Use with TEvenTrueUserFilterRule"""

    call_count = 0

    def check_result(zipped_user_bool):
        nonlocal call_count
        # [0] is a user instance
        assert zipped_user_bool[0].id == call_count
        # [1] is filter result of this user
        assert zipped_user_bool[1] is (call_count % 2 == 0)
        call_count += 1
        check_result.call_count = call_count

    return check_result


@pytest.fixture
def always_true_zipped_result_checker():
    call_count = 0

    def check_result(zipped_user_bool):
        nonlocal call_count
        # [0] is a user instance
        assert zipped_user_bool[0].id == call_count
        # [1] is filter result of this user
        # It's RuleResult type, so we need bool() function to convert
        assert bool(zipped_user_bool[1]) is True
        call_count += 1
        check_result.call_count = call_count

    return check_result


def test_required_fields_validation(clean_config_parser):
    ConfigParser.parse({'user_plan': ''}, Plan)
    error = ConfigParser.errors()[0]
    # the error message looks like:
    assert_that(str(error), all_of(contains_string('required'),
                                   contains_string('from'),
                                   contains_string('do')))


def test_filtering_with_filter_rule(even_true_zipped_result_checker):
    plan = ConfigParser.parse({'user_plan': 'plan name',
                               'from': [{'psr': {'num': 3}}],
                               'that': [{'otf': {}}],
                               'do': []}, Plan)

    # type check
    assert plan.name == 'plan name'
    assert isinstance(plan.sources, UserSourceRuleAnyOfSet)
    assert isinstance(plan.sources.rules[0], TUserSourceRule)
    assert isinstance(plan.filters, UserFilterRuleAnyOfSet)
    assert isinstance(plan.filters.immediate_rules[0], TEvenTrueUserFilterRule)

    plan._UserPlan__filtering().pipe(op.do(rx.Observer(on_next=even_true_zipped_result_checker))).run()
    assert even_true_zipped_result_checker.call_count == 3


def test_filtering_without_filter_rule(always_true_zipped_result_checker):
    plan = ConfigParser.parse({'user_plan': 'plan name',
                               'from': [{'psr': {'num': 3}}],
                               'do': []}, Plan)

    plan._UserPlan__filtering().pipe(op.do(rx.Observer(on_next=always_true_zipped_result_checker))).run()
    assert always_true_zipped_result_checker.call_count == 3
