from typing import Any, List, Dict

from puntgun import util
from puntgun.base.options import ListOption, Field, MapOption
from puntgun.option.filter_rule import FilterRule


class RuleSet(ListOption):
    """
    Abstract class for representing a option set.
    """
    config_keyword = "generic-option-set"


RuleSet.valid_options = [Field.of('name', str, singleton=True), RuleSet, FilterRule]


class AllOfRuleSet(RuleSet):
    config_keyword = "all-of"
    logger = util.get_logger(__qualname__)


class AnyOfRuleSet(RuleSet):
    config_keyword = "any-of"
    logger = util.get_logger(__qualname__)


class WightCondition(MapOption):
    config_keyword = "condition"
    logger = util.get_logger(__qualname__)
    valid_options = [Field.of("wight", int, required=True, singleton=True), FilterRule]

    def __init__(self, config_value: Dict[str, Any]):
        other_keywords = [key for key in config_value.keys() if key != 'wight']
        assert len(other_keywords) == 1, \
            f"Option [{self}]: must have exact one filter option, but found {len(other_keywords)}."

        # the config_value should be something like:
        # {"wight":1, "a-filter-option-keyword": option-value}
        # we need to assign that option's instance to a known attribute,
        # or we don't know how to access it once exit __init__ method.
        rule_keyword = other_keywords[0]

        # let the super class build the option's instance
        super().__init__(config_value)

        # assign that instance to a known attribute
        self.rule = getattr(self, rule_keyword)


class WightOfRuleSet(RuleSet):
    config_keyword = "wight-of"
    logger = util.get_logger(__qualname__)
    valid_options = [Field.of('name', str, singleton=True),
                     Field.of("goal", int, required=True, singleton=True),
                     WightCondition]

    def __init__(self, config_value: List[Any]):
        super().__init__(config_value)
        self.__check_goal_constraints()

    @util.log_error_with(logger)
    def __check_goal_constraints(self):
        # the self.goal value type will be a singleton-list after initialized.
        # extract the element for convenience
        self.goal = self.goal[0]

        sum_of_wight = sum([c.wight for c in self.condition])
        assert sum_of_wight >= self.goal, \
            f"Option [{self}]: The sum of all conditions' wight (current:{sum_of_wight}) " \
            f"must be greater than the goal (current:{self.goal}), " \
            f"or you will never trigger this option set."
