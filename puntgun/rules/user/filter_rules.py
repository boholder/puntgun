import abc
from typing import ClassVar

from rules import NumericFilterRule
from rules.user import User


class UserFilterRule(abc.ABC):
    """
    Holds a set of value from plan configuration for constructing a predicative rule.
    Takes **one** :class:`User` instance each time and judges if this user's data triggers(meets) its condition.
    """


class FollowerUserFilterRule(NumericFilterRule, UserFilterRule):
    """Check user's follower count."""
    _keyword: ClassVar[str] = 'follower'

    def __call__(self, user: User):
        return super().compare(user.followers_count)


class FollowingUserFilterRule(NumericFilterRule, UserFilterRule):
    """Check user's following count."""
    _keyword: ClassVar[str] = 'following'

    def __call__(self, user: User):
        return super().compare(user.following_count)
