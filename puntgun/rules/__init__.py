import abc
import importlib
import inspect
import pkgutil
import sys
from typing import List, ClassVar, TypeVar

from pydantic import BaseModel, root_validator, ValidationError

import rules


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
    A rule that checks if a numeric value inside a pre-set range (min < v < max).
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


def import_rule_classes():
    """This logic worth an independent function"""
    ?怎么实现

import_rule_classes()


class ConfigParser(object):
    # There are only once parsing process for each run,
    # so I guess it's ok to use a class variable to store the errors,
    # and use this class as singleton pattern.
    # Sort of inconvenient when unit testing.
    _errors: List[Exception] = []

    _T = TypeVar('_T', bound=FromConfig)

    @staticmethod
    def parse(conf: dict, expected_type: _T):
        """
        Take a piece of configuration and the expected type from caller,
        recognize which rule it is and parse it into corresponding rule instance.
        Only do the find & parse work, won't construct them into cascade component instances.

        Collect errors occurred during parsing,
        by this way we won't break the whole parsing process with error raising.
        So that we can report all errors at once after finished all parsing work
        and the user can fix them at once without running over again for configuration validation.
        """

        def generate_placeholder_instance():
            """
            Return a placeholder instance which inherits from the given expected class.
            For letting caller continue parsing.
            """
            return type('FakeSubclassOf' + expected_type.__name__, (expected_type,), {})()

        for subclass in expected_type.__subclasses__():
            if subclass.keyword() in conf:
                try:
                    # let the subclass itself decide how to parse
                    return subclass.parse_from_config(conf)
                except ValidationError as e:
                    # catch validation exceptions raised by pydantic and store them
                    ConfigParser._errors.append(e)
                    return generate_placeholder_instance()

        ConfigParser._errors.append(
            ValueError(f"Can't find the rule of the [{expected_type}] type from configuration: {conf}"))

        return generate_placeholder_instance()

    @staticmethod
    def errors():
        return ConfigParser._errors

    @staticmethod
    def clear_errors():
        ConfigParser._errors = []
