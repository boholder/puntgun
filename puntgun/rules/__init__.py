import sys
from typing import Type, Optional

from pydantic import BaseModel, root_validator


class Rule(BaseModel):
    """
    A template class for rule parsing, representing a rule that can be parsed from configuration.
    """
    keyword: Optional[str] = ''

    @classmethod
    def parse_from_config(cls, conf: dict):
        """
        Some rules declare fields which names are not the same as the configuration.
        For example, the plan has a 'from' field which is a reserved keyword in Python.
        So we need this adapter method to custom the parsing process when necessary.
        """
        return cls.parse_obj(conf)


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


def parse_one(conf: dict, expected_type: Type[Rule]):
    """
    Take a piece of configuration and the expected type from caller,
    recognize which rule it is and parse it into corresponding rule instance.
    Only do the parsing work, won't construct them into cascade component instances.
    """

    for subclass in expected_type.__subclasses__():
        if conf[subclass.keyword]:
            return subclass.parse_from_config(conf)
    raise ValueError(f"Can't recognize the configuration: {conf} as a {expected_type}.")
