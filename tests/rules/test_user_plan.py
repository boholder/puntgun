import pytest
import reactivex as rx
from hamcrest import assert_that, contains_string, all_of
from reactivex import operators as op

from puntgun.record import Record
from puntgun.rules import Plan, RuleResult
from puntgun.rules.config_parser import ConfigParser
from puntgun.rules.user import User
from puntgun.rules.user.action_rules import UserActionRule
from puntgun.rules.user.filter_rules import UserFilterRule
from puntgun.rules.user.plan import UserPlanResult
from puntgun.rules.user.rule_sets import UserSourceRuleResultMergingSet, UserFilterRuleAnyOfSet
from puntgun.rules.user.source_rules import UserSourceRule


class TRule(UserActionRule, UserFilterRule):
    _keyword = "ptr"
    field_a: str


class TestUserPlanResult:
    def test_to_record(self):
        actual = UserPlanResult(
            plan_id=123,
            user=User(id=1, username="uname"),
            filtering_result=RuleResult.true(TRule(field_a="a")),
            action_results=[RuleResult.true(TRule(field_a="b"))],
        ).to_record()
        expect = Record(
            type="user_plan_result",
            data={
                "plan_id": 123,
                "user": {"id": 1, "username": "uname"},
                "decisive_filter_rule": {"keyword": "ptr", "value": "field_a=a"},
                "action_rule_results": [{"keyword": "ptr", "value": "field_a=a", "done": True}],
            },
        )

        assert actual.__eq__(expect)

    def test_parse_from_record(self):
        actual = UserPlanResult.parse_from_record(
            Record(
                type="user_plan_result",
                data={
                    "plan_id": 123,
                    "user": {"id": 1, "username": "uname"},
                    "decisive_filter_rule": {"keyword": "ptr", "value": "field_a=a"},
                    "action_rule_results": [{"keyword": "ptr", "value": "field_a=a", "done": False}],
                },
            )
        )

        expect = UserPlanResult(
            plan_id=123,
            user=User(id=1, username="uname"),
            filtering_result=RuleResult.true(None),
            action_results=[RuleResult.false(TRule(field_a="b"))],
        )

        assert actual.__eq__(expect)


# == things for testing user plan ==


class TUserSourceRule(UserSourceRule):
    # DO NOT make the keyword same as any other test rules.
    # Or it may fail test cases that are checking instances type,
    # because the :class:`ConfigParser` may wrongly choose
    # not-in-this-file test rules with same keyword.
    _keyword = "psr"
    num: int

    def __call__(self):
        return rx.from_iterable([User(id=i) for i in range(self.num)])


class TEvenTrueUserFilterRule(UserFilterRule):
    _keyword = "etf"

    def __call__(self, user: User):
        return RuleResult(self, user.id % 2 == 0)


@pytest.fixture
def even_true_zipped_result_checker():
    """Use with TEvenTrueUserFilterRule"""

    call_count = 0

    def check_result(zipped_user_bool):
        nonlocal call_count
        # [0] is a user instance
        assert zipped_user_bool[0].id == call_count
        # [1] is filter result of this user
        assert bool(zipped_user_bool[1]) is (call_count % 2 == 0)
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
        assert isinstance(zipped_user_bool[1], RuleResult)
        assert bool(zipped_user_bool[1]) is True

        # update counter
        call_count += 1
        check_result.call_count = call_count

    return check_result


class TUserActionRule(UserActionRule):
    _keyword = "ptuar"

    will_return: bool

    def __call__(self, user: User):
        return RuleResult(self, self.will_return)


@pytest.fixture
def user_plan_result_checker():
    call_count = 0

    def check_result(user_plan_result: UserPlanResult):
        # [1] is filter result of this user
        # It's RuleResult type, so we need bool() function to convert
        assert isinstance(user_plan_result.filtering_result, RuleResult)
        assert bool(user_plan_result.filtering_result) is True

        # [2] is a list of action results
        # We arranged one always-true action and one always-false action
        assert len([r for r in user_plan_result.action_results if bool(r) is True]) == 1
        assert len([r for r in user_plan_result.action_results if bool(r) is False]) == 1

        # update counter
        nonlocal call_count
        call_count += 1
        check_result.call_count = call_count

    return check_result


class TestUserPlan:
    def test_required_fields_validation(self, clean_config_parser_errors):
        ConfigParser.parse({"user_plan": ""}, Plan)
        error = ConfigParser.errors()[0]
        # the error message looks like:
        assert_that(str(error), all_of(contains_string("required"), contains_string("from"), contains_string("do")))

    def test_filtering_with_filter_rule(self, even_true_zipped_result_checker):
        plan = ConfigParser.parse(
            {"user_plan": "plan name", "from": [{"psr": {"num": 3}}], "that": [{"etf": {}}], "do": []}, Plan
        )

        # type check
        assert plan.name == "plan name"
        assert isinstance(plan.sources, UserSourceRuleResultMergingSet)
        assert isinstance(plan.sources.rules[0], TUserSourceRule)
        assert isinstance(plan.filters, UserFilterRuleAnyOfSet)
        assert isinstance(plan.filters.immediate_rules[0], TEvenTrueUserFilterRule)

        plan._filtering().pipe(op.do(rx.Observer(on_next=even_true_zipped_result_checker))).run()
        assert even_true_zipped_result_checker.call_count == 3

    def test_filtering_without_filter_rule(self, always_true_zipped_result_checker):
        plan = ConfigParser.parse({"user_plan": "plan name", "from": [{"psr": {"num": 3}}], "do": []}, Plan)

        plan._filtering().pipe(op.do(rx.Observer(on_next=always_true_zipped_result_checker))).run()
        assert always_true_zipped_result_checker.call_count == 3

    def test_plan_running(self, user_plan_result_checker):
        plan = ConfigParser.parse(
            {
                "user_plan": "plan name",
                "from": [{"psr": {"num": 3}}],
                "that": [{"etf": {}}],
                "do": [{"ptuar": {"will_return": True}}, {"ptuar": {"will_return": False}}],
            },
            Plan,
        )

        plan().pipe(op.do(rx.Observer(on_next=user_plan_result_checker))).run()

        # due to the effect of TEvenTrueUserFilterRule,
        # test user with id=1 is thrown away and won't be applied actions
        # and users that id=0,2 are remained
        assert user_plan_result_checker.call_count == 2
