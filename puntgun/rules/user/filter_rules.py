from typing import ClassVar

from reactivex import Observable

from rules import NumericFilterRule, FromConfig
from rules.user import User


class UserFilterRule(FromConfig):
    """
    Holds a set of value from plan configuration for constructing a predicative rule.
    Takes **one** :class:`User` instance each time and judges if this user's data triggers(meets) its condition.
    """

    def __call__(self, user: User) -> bool | Observable[bool]:
        """
        Immediate filter rules will directly return a raw boolean value,
        while slow filter rules (marked with :class:`NeedClient`) and filter rule sets
        will return a reactivex :class:`Observable` which wraps a boolean value.
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
