import sys

from pydantic import BaseModel, root_validator

from rules.user import User


class UserFilterRule(object):
    """
    Holds a set of value from plan configuration for constructing a predicative rule.
    Takes **one** user instance each time and judges if this user's data triggers(fits) its condition.
    """


class NumericUserFilterRule(BaseModel):
    """
    A rule that checks if a user's numeric data fits a certain condition.
    """
    less_than = float(sys.maxsize)
    more_than = float(-sys.maxsize - 1)

    @root_validator(pre=True)
    def there_should_be_fields(cls, values):
        if not values.get('less_than') and not values.get('more_than'):
            raise ValueError('At least one of "less_than" or "more_than" should be specified.')
        return values

    @root_validator
    def compare(cls, values):
        lt, mt = values.get('less_than'), values.get('more_than')
        if lt <= mt:
            raise ValueError(f"'less_than'({lt}) should be bigger than 'more_than'({mt})")
        return values

    def judge(self, num):
        return self.more_than < num < self.less_than


class FollowerUserFilterRule(NumericUserFilterRule, UserFilterRule):
    """Check user's follower count."""

    def __call__(self, user: User):
        return super().judge(user.followers_count)


class FollowingUserFilterRule(NumericUserFilterRule, UserFilterRule):
    """Check user's following count."""

    def __call__(self, user: User):
        return super().judge(user.following_count)
