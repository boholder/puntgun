import datetime
import itertools

import pydantic
import pytest
from hamcrest import all_of, assert_that, contains_string

from puntgun import rules
from puntgun.rules import (
    FromConfig,
    NumericRangeFilterRule,
    Plan,
    RuleResult,
    TemporalRangeFilterRule,
)
from puntgun.rules.config_parser import ConfigParser


class TestRuleType:
    pass


class TestConfigParserWithRuleBaseClass:
    class TRule(FromConfig, TestRuleType):
        _keyword = "key"
        f: int

    def test_config_parsing_success(self):
        obj = ConfigParser.parse({"key": {"f": 123}}, TestRuleType)
        assert obj.f == 123

    def test_config_parsing_failure(self, clean_config_parser_errors):
        # can't find the TestRule base on an empty dict
        # will return a placeholder instance which inherits from the given expected class.
        place_holder_instance = ConfigParser.parse({}, TestRuleType)
        assert issubclass(type(place_holder_instance), TestRuleType)
        assert_that(str(ConfigParser.errors()[0]), all_of(contains_string("{}"), contains_string("TestRuleType")))

    def test_handle_validation_exception(self, clean_config_parser_errors):
        place_holder_instance = ConfigParser.parse(
            {"key": {"f": "wrong_type_value_triggers_pydantic_validation_exception"}}, TestRuleType
        )
        assert issubclass(type(place_holder_instance), TestRuleType)
        assert_that(str(ConfigParser.errors()[0]), contains_string("validation"))


class TestRuleResult:
    def test_getting_both_result_and_rule_instance_inside(self):
        fake_rule_instance = object()
        r = RuleResult(fake_rule_instance, True)
        assert r.rule is fake_rule_instance
        assert bool(r) is True


class TestPlan:
    def test_incremental_id(self):
        class P(Plan):
            pass

        # avoid other test cases affection, reset the counter
        rules.plan_id_iter = itertools.count()

        assert P(name="").id == 0
        assert P(name="").id == 1
        assert P(name="").id == 2


class TestConflictCheckFunction:
    def test_three_groups_conflict(self):
        values = {"a": 1, "b": 2, "c": 3, "d": 4}
        # the field "e" isn't configured in "values", so it shouldn't show in error message.
        conflict_field_groups = [["a", "b", "e"], ["c"], ["d"]]
        with pytest.raises(ValueError) as e:
            rules.validate_fields_conflict(values, conflict_field_groups)

        assert_that(
            str(e).replace(" ", ""),
            all_of(
                contains_string("conflict"),
                contains_string("(['a','b'],['c'])"),
                contains_string("(['a','b'],['d'])"),
                contains_string("(['c'],['d'])"),
            ),
        )

    def test_two_groups_conflict(self):
        values = {"a": 1, "b": 2, "c": 3, "d": 4}
        # the field "e" isn't configured in "values", so it shouldn't show in error message.
        conflict_field_groups = [["a", "b", "e"], ["c", "d"]]
        with pytest.raises(ValueError) as e:
            rules.validate_fields_conflict(values, conflict_field_groups)

        assert_that(
            str(e).replace(" ", ""), all_of(contains_string("conflict"), contains_string("(['a','b'],['c','d'])"))
        )

    def test_no_conflict(self):
        values = {"a": 1, "b": 2}
        conflict_field_groups = [["a", "b"], ["c"]]
        rules.validate_fields_conflict(values, conflict_field_groups)
        # values not change
        assert values == {"a": 1, "b": 2}


class TestNumericRangeFilterRule:
    @pytest.fixture
    def rule(self):
        return lambda conf: NumericRangeFilterRule.parse_obj(conf)

    def test_no_field_configured_will_raise_exception(self, rule):
        with pytest.raises(pydantic.ValidationError) as e:
            print(rule({}))
        assert_that(str(e), contains_string("field"))

    def test_check_invalid_edge_value(self, rule):
        with pytest.raises(pydantic.ValidationError) as e:
            rule({"more_than": 10, "less_than": 5})
        assert_that(str(e), contains_string("Invalid range"))

    def test_single_less_than(self, rule):
        r = rule({"less_than": 10})
        assert r.compare(5)
        assert not r.compare(20)

    def test_single_more_than(self, rule):
        r = rule({"more_than": 10})
        assert r.compare(20)
        assert not r.compare(5)

    def test_both_less_more(self, rule):
        r = rule({"less_than": 20, "more_than": 10})
        assert r.compare(15)
        assert not r.compare(5)
        assert not r.compare(25)
        # edge cases (equal) result in False.
        assert not r.compare(10)
        assert not r.compare(20)


class TestTemporalRangeFilterRule:
    @pytest.fixture
    def rule(self):
        return lambda conf: TemporalRangeFilterRule.parse_obj(conf)

    def test_no_field_configured_will_raise_exception(self, rule):
        with pytest.raises(pydantic.ValidationError) as e:
            print(rule({}))
        assert_that(str(e), contains_string("field"))

    def test_check_invalid_edge_value(self, rule):
        time = datetime.datetime.utcnow()
        with pytest.raises(pydantic.ValidationError) as e:
            rule({"after": time, "before": time - datetime.timedelta(hours=1)})
        assert_that(str(e), contains_string("Invalid range"))

    def test_single_after(self, rule):
        time = datetime.datetime.utcnow()
        timedelta = datetime.timedelta(hours=1)
        r = rule({"after": time})
        assert r.compare(time + timedelta)
        assert not r.compare(time - timedelta)

    def test_single_before(self, rule):
        time = datetime.datetime.utcnow()
        timedelta = datetime.timedelta(hours=1)
        r = rule({"before": time})
        assert r.compare(time - timedelta)
        assert not r.compare(time + timedelta)

    def test_before_after(self, rule):
        time = datetime.datetime.utcnow()
        timedelta = datetime.timedelta(hours=1)
        # -1 <-> 1
        r = rule({"after": time - timedelta, "before": time + timedelta})
        # 0, pass
        assert r.compare(time)
        # 2, -2, fail
        assert not r.compare(time + timedelta * 2)
        assert not r.compare(time - timedelta * 2)
