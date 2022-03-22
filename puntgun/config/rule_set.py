from typing import Any, List

from puntgun import util
from puntgun.config.config_option import ListOption, Field, MapOption
from puntgun.config.filter_rule import FilterRule, NameField


class RuleSet(ListOption):
    """
    Abstract class for representing a rule set.
    """
    config_keyword = "generic-rule-set"
    logger = util.get_logger(__qualname__)

    def __init__(self, config_value: List[Any]):
        super().__init__(config_value)
        self.__check_name_field_must_be_one_if_exists()

    @util.log_error_with(logger)
    def __check_name_field_must_be_one_if_exists(self):
        if hasattr(self, "name"):
            assert len(self.name) == 1, \
                f"Option [{self}]: can only have one name field, but found {len(self.name)}."


RuleSet.valid_options = [NameField, *RuleSet.__subclasses__(), *FilterRule.__subclasses__()]


class AllOfRuleSet(RuleSet):
    config_keyword = "all-of"
    logger = util.get_logger(__qualname__)

    def __init__(self, config_value: List[Any]):
        super().__init__(config_value)


class AnyOfRuleSet(RuleSet):
    config_keyword = "any-of"
    logger = util.get_logger(__qualname__)

    def __init__(self, config_value: List[Any]):
        super().__init__(config_value)


class WightCondition(MapOption):
    config_keyword = "condition"
    logger = util.get_logger(__qualname__)
    valid_options = [Field.of("wight", int, required=True), *FilterRule.__subclasses__()]


class WightOfRuleSet(RuleSet):
    config_keyword = "wight-of"
    logger = util.get_logger(__qualname__)
    valid_options = [Field.of("goal", int, required=True), WightCondition]

    def __init__(self, config_value: List[Any]):
        super().__init__(config_value)
        self.__check_custom_constraints()

    @util.log_error_with(logger)
    def __check_custom_constraints(self):
        sum_of_wight = sum([c.wight for c in self.condition])
        assert sum_of_wight > self.goal, \
            f"Option [{self}]: The sum of all conditions' wight (current:{sum_of_wight}) " \
            f"must be greater than the goal (current:{self.goal}), " \
            f"or you will never trigger this rule set."
