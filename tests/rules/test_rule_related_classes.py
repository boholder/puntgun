import pytest
from hamcrest import assert_that, contains_string, all_of

from rules import Rule, ConfigParser


class TestRuleType:
    pass


class TestConfigParserWithRuleBaseClass:
    class TestRule(Rule, TestRuleType):
        _keyword = 'f'
        f: int

    @pytest.fixture(autouse=True)
    def clean_config_parser(self):
        ConfigParser.clear_errors()

    def test_config_parsing_success(self):
        obj = ConfigParser.parse({'f': 123}, TestRuleType)
        assert obj.f == 123

    def test_config_parsing_failure(self):
        # can't find the TestRule base on an empty dict
        # will return a placeholder instance which inherits from the given expected class.
        place_holder_instance = ConfigParser.parse({}, TestRuleType)
        assert issubclass(type(place_holder_instance), TestRuleType)
        assert_that(str(ConfigParser.errors()[0]), all_of(contains_string('{}'), contains_string('TestRuleType')))

    def test_handle_validation_exception(self):
        place_holder_instance = ConfigParser.parse(
            {'f': 'wrong_type_value_triggers_pydantic_validation_exception'}, TestRuleType)
        assert issubclass(type(place_holder_instance), TestRuleType)
        assert_that(str(ConfigParser.errors()[0]), contains_string('validation'))
