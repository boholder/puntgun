"""
I'm using this file as util module for rule stuff.
"""
import abc
import datetime
import itertools
import sys
from typing import ClassVar, List

from pydantic import BaseModel, root_validator, Field
from reactivex import Observable


class FromConfig(BaseModel, abc.ABC):
    """
    A base class for rule parsing, representing a rule that can be parsed from configuration.
    """

    # Works like index of rule classes,
    # help the :class:`ConfigParser` to recognize which class it should pick according to the configuration.
    _keyword: ClassVar[str] = "corresponding_rule_name_in_config_of_this_rule"

    @classmethod
    def parse_from_config(cls, conf: dict | str):
        """
        Most rules have a dictionary structure of fields, their configurations are something like:
        { 'rule_name': {'field_1':1, 'field_2':2,...} }
        Take this format as the default logic so most rules needn't override this function.

        There are some special cases when parsing a rule from configuration.
        For example, some rules declare fields which names are not the same as the configuration:
        the plan type has a 'from' field which is a reserved keyword in Python.
        Some rules' config texts only contain their string type keywords, not even a dictionary.

        Anyway, we need this polymorphic method to let rules to custom their parsing processes.
        """
        return cls.parse_obj(conf[cls._keyword])

    @classmethod
    def keyword(cls):
        return cls._keyword

    class Config:
        """https://pydantic-docs.helpmanual.io/usage/models/#private-model-attributes"""

        underscore_attrs_are_private = True


plan_id_iter = itertools.count()


def generate_id():
    return next(plan_id_iter)


class Plan(FromConfig):
    """This class exists only for :class:`ConfigParser` to recognize plan classes."""

    # User will give each plan a human-readable name in plan configuration,
    # set it when parsing instance.
    # Default value for not letting pydantic raise validation error.
    name: str = ""

    # We need this incremental id field to abbreviate plan information to
    # a "database foreign key purpose" plan_id,
    # and add this plan_id to every record that generated by corresponding plan.
    #
    # By doing so we:
    # 1. Won't lose records' parent plan information.
    # 2. Also needn't put records under their plan's json output
    #    (if we don't have this order field, we need to do this to guarantee require no.1),
    #    so we can output records from any plan at any time,
    #    no worry about chronological writing or writing in particular order
    #    in order to output a correct json structure.
    #
    # https://pydantic-docs.helpmanual.io/usage/models/#field-with-dynamic-default-value
    id: int = Field(default_factory=generate_id)

    def __call__(self) -> Observable:
        raise NotImplementedError


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

    rule: FromConfig
    result: bool

    def __init__(self, rule: FromConfig, result: bool):
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


def validate_required_fields_exist(rule_keyword, conf: dict, required_field_names: [str]):
    """
    Custom configuration parsing process
    - :class:`ConfigParser` sort of bypass the pydantic library's validation,
    so we need to put custom validation inside the custom parsing process when necessary.
    """
    missing = []
    for k in required_field_names:
        if k not in conf:
            missing.append(k)

    # point out all errors at once
    if missing:
        raise ValueError(f"Missing required field(s) {missing} " f"in configuration [{rule_keyword}]: {conf}")


def validate_fields_conflict(values, field_groups: List[List[str]]):
    # only fields that are configured will be count in.
    for i in range(len(field_groups)):
        field_groups[i] = [f for f in field_groups[i] if values.get(f)]

    conflicts = []
    # two-by-two compare
    while len(field_groups) > 1:
        # take first group to compare other groups
        sample_group = field_groups[0]

        for group in field_groups[1:]:
            # check if both two conflict group have fields that have been configured
            if any(values.get(f) for f in sample_group) and any(values.get(f) for f in group):
                conflicts.append((sample_group, group))

        # remove completed group
        field_groups = field_groups[1:]

    if len(conflicts) > 0:
        raise ValueError(
            f"Configured fields have conflicts, you should chose one group of fields "
            f"to configurate in each conflict: {conflicts}"
        )

    return values


class FieldsRequired(BaseModel):
    @root_validator(pre=True)
    def there_should_be_fields(cls, values):
        if len(values) == 0:
            raise ValueError("At least one field should be configured.")
        return values


class NumericRangeFilterRule(FromConfig, FieldsRequired):
    """
    A filter rule delegating agent that
    checks if-within-a-range (min < v < max) of a numeric value.
    Equal-to-edge cases are regard as falsy.
    """

    less_than = float(sys.maxsize)
    more_than = float(-sys.maxsize - 1)

    @root_validator
    def validate_config(cls, values):
        lt, mt = values.get("less_than"), values.get("more_than")
        if lt <= mt:
            raise ValueError(f"Invalid range, right 'less_than'({lt}) " f"should be bigger than left 'more_than'({mt})")
        return values

    def compare(self, num):
        return self.more_than < num < self.less_than


class TemporalRangeFilterRule(FromConfig, FieldsRequired):
    """
    Temporal value version of within-range checking agent.
    """

    before = datetime.datetime.max
    after = datetime.datetime.min

    @root_validator
    def validate_config(cls, values):
        b, a = values.get("before"), values.get("after")
        if b <= a:
            raise ValueError(f"Invalid range, right time 'before'({b}) " f"should be after left time 'after'({a})")
        return values

    def compare(self, time):
        return self.after < time < self.before
