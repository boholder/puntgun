import pytest
from hamcrest import assert_that, contains_string, all_of
from pydantic import ValidationError

from rules import FromConfig, NumericFilterRule
from rules.config_parser import ConfigParser


class TestRuleType:
    pass


class TestConfigParserWithRuleBaseClass:
    class TestRule(FromConfig, TestRuleType):
        _keyword = 'key'
        f: int

    def test_config_parsing_success(self):
        obj = ConfigParser.parse({'key': {'f': 123}}, TestRuleType)
        assert obj.f == 123

    def test_config_parsing_failure(self, clean_config_parser):
        # can't find the TestRule base on an empty dict
        # will return a placeholder instance which inherits from the given expected class.
        place_holder_instance = ConfigParser.parse({}, TestRuleType)
        assert issubclass(type(place_holder_instance), TestRuleType)
        assert_that(str(ConfigParser.errors()[0]), all_of(contains_string('{}'), contains_string('TestRuleType')))

    def test_handle_validation_exception(self, clean_config_parser):
        place_holder_instance = ConfigParser.parse(
            {'key': {'f': 'wrong_type_value_triggers_pydantic_validation_exception'}}, TestRuleType)
        assert issubclass(type(place_holder_instance), TestRuleType)
        assert_that(str(ConfigParser.errors()[0]), contains_string('validation'))


class TestNumericUserFilterRule:
    @pytest.fixture
    def rule(self):
        return lambda obj: NumericFilterRule.parse_obj(obj)

    def test_check_number_order(self, rule):
        with pytest.raises(ValidationError) as actual_error:
            rule({'more_than': 10, 'less_than': 5})
        assert_that(str(actual_error.value), contains_string('than'))

    def test_single_less_than(self, rule):
        r = rule({'less_than': 10})
        assert r.compare(5)
        assert not r.compare(20)

    def test_single_more_than(self, rule):
        r = rule({'more_than': 10})
        assert r.compare(20)
        assert not r.compare(5)

    def test_both_less_more(self, rule):
        r = rule({'less_than': 20, 'more_than': 10})
        assert r.compare(15)
        assert not r.compare(5)
        assert not r.compare(25)
        # edge case (equal) result in False.
        assert not r.compare(10)
        assert not r.compare(20)
