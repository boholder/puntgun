import sys
from typing import Type, Optional, List

from pydantic import BaseModel, root_validator


class Rule(BaseModel):
    """
    A template class for rule parsing, representing a rule that can be parsed from configuration.
    """
    keyword: Optional[str] = ''

    @classmethod
    def parse_from_config(cls, conf: dict):
        """
        There are some special cases when parsing a rule from configuration.
        For example, some rules declare fields which names are not the same as the configuration:
        the plan type has a 'from' field which is a reserved keyword in Python.

        Anyway, we need this polymorphic method to let rules to custom their parsing processes.
        """
        return cls.parse_obj(conf)


class ConfigParser(object):
    __errors: List[Exception] = []

    @staticmethod
    def parse(conf: dict, expected_type: Type[Rule]):
        """
        Take a piece of configuration and the expected type from caller,
        recognize which rule it is and parse it into corresponding rule instance.
        Only do the find & parse work, won't construct them into cascade component instances.

        Collect errors occurred during parsing,
        by this way we won't break the whole parsing process with error raising.
        So that we can report all errors at once after finished all parsing
        and user can fix them at once without running over again for configuration validation.
        """

        for subclass in expected_type.__subclasses__():
            if subclass.keyword in conf:
                try:
                    # let the subclass itself decide how to parse
                    return subclass.parse_from_config(conf)
                except Exception as e:
                    # catch validation exceptions raised by pydantic and store them
                    ConfigParser.__errors.append(e)
                    return None

        ConfigParser.__errors.append(
            ValueError(f"Can't parse this to the [{expected_type}] type: {conf}"))

    @staticmethod
    def get_errors():
        return ConfigParser.__errors


class NumericFilterRule(Rule):
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
