import sys

from pydantic import BaseModel, root_validator


class Rule(object):
    """
    How
    """


class NumericFilterRule(BaseModel):
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
