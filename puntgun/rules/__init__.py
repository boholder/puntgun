"""
I'm using this file as util module for rule stuff.
"""
import abc
import sys
from typing import ClassVar

from pydantic import BaseModel, root_validator


class FromConfig(BaseModel, abc.ABC):
    """
    A base class for rule parsing, representing a rule that can be parsed from configuration.
    """

    # Works like index of rule classes,
    # help the :class:`ConfigParser` to recognize which class it should pick according to the configuration.
    _keyword: ClassVar[str] = 'corresponding_rule_name_in_config_of_this_rule'

    @classmethod
    def parse_from_config(cls, conf: dict):
        """
        Most rules have a dictionary structure of fields, their configuration is something like:
        { 'rule_name': {'field_1':1, 'field_2':2,...} }
        Take this format as the default logic so most rules needn't override this function.

        There are some special cases when parsing a rule from configuration.
        For example, some rules declare fields which names are not the same as the configuration:
        the plan type has a 'from' field which is a reserved keyword in Python.

        Anyway, we need this polymorphic method to let rules to custom their parsing processes.
        """
        return cls.parse_obj(conf[cls._keyword])

    @classmethod
    def keyword(cls):
        return cls._keyword

    class Config:
        """https://pydantic-docs.helpmanual.io/usage/models/#private-model-attributes"""
        underscore_attrs_are_private = True


class NumericFilterRule(FromConfig):
    """
    A filter rule that checks if a numeric value inside a pre-set range (min < v < max).
    As you see, edge cases (equal) are falsy.
    """
    less_than = float(sys.maxsize)
    more_than = float(-sys.maxsize - 1)

    @root_validator(pre=True)
    def there_should_be_fields(cls, values):
        if not values.get('less_than') and not values.get('more_than'):
            raise ValueError('At least one of "less_than" or "more_than" should be specified.')
        return values

    @root_validator
    def validate_two_edges(cls, values):
        lt, mt = values.get('less_than'), values.get('more_than')
        if lt <= mt:
            raise ValueError(f"'less_than'({lt}) should be bigger than 'more_than'({mt})")
        return values

    def compare(self, num):
        return self.more_than < num < self.less_than


def validate_required_fields_exist(rule_keyword, conf: dict, required_field_names: [str]):
    """
    Custom configuration parsing process - :class:`ConfigParser` sort of bypass the pydantic library's
    validation, so we need to put custom validation inside the custom parsing process when necessary.
    """
    missing = []
    for k in required_field_names:
        if k not in conf:
            missing.append(k)

    # point out all errors at once
    if missing:
        raise ValueError(f"Missing required field(s) {missing} in configuration [{rule_keyword}]: {conf}")


class Plan(FromConfig):
    """This class exists only for :class:`ConfigParser` to recognize plan classes."""


class RuleResult(object):
    """
    It's a special wrapper as filter/action rules' execution result.
    After a rule's execution, it returns an instance of this class instead of directly return the boolean value,
    zipping the rule instance itself with its boolean type filtering/operation result into one.

    It's for constructing execution report that need to tell
    WHICH filter rule is triggered or WHICH action rule is successfully executed.

    Rather than using tuple structure,
    we can simplify the logic by using bool(<result>) to get the boolean result
    (python will automatically do that for us)
    without extract/map the tuple before processing, so we can change lesser present code.
    """

    def __init__(self, rule, result: bool):
        self.rule = rule
        self.result = result

    def __bool__(self):
        return self.result

    @staticmethod
    def true(rule):
        return RuleResult(rule, True)

    @staticmethod
    def false(rule):
        return RuleResult(rule, False)
