import datetime
import re
from typing import ClassVar

from reactivex import Observable

from rules import NumericRangeFilterRule, FromConfig, RuleResult, TemporalRangeFilterRule
from rules.user import User


class UserFilterRule(FromConfig):
    """
    Holds a set of value from plan configuration for constructing a predicative rule.
    Takes **one** :class:`User` instance each time and judges if this user's data triggers(meets) its condition.
    """

    def __call__(self, user: User) -> RuleResult | Observable[RuleResult]:
        """
        Immediate filter rules will directly return a raw boolean value,
        while slow filter rules (marked with :class:`NeedClient`) and filter rule sets
        will return a reactivex :class:`Observable` which wraps a :class:`RuleResult` value.
        """


class PlaceHolderUserFilterRule(UserFilterRule):
    """
    In user plan, the filter rule is optional,
    but we need a default dummy placeholder for an executable user plan.
    Here is the default one which will let all users from source trigger it
    so actions can apply on all users.
    """
    _keyword = 'placeholder_user_filter_rule'

    def __call__(self, user: User):
        return RuleResult.true(self)


class FollowerUserFilterRule(NumericRangeFilterRule, UserFilterRule):
    """Check user's follower count."""
    _keyword: ClassVar[str] = 'follower'

    def __call__(self, user: User):
        return RuleResult(self, super().compare(user.followers_count))


class ShortenFollowerUserFilterRule(UserFilterRule):
    _keyword: ClassVar[str] = 'follower_less_than'

    @classmethod
    def parse_from_config(cls, conf: dict):
        return FollowerUserFilterRule(less_than=conf[cls._keyword])


class FollowingUserFilterRule(NumericRangeFilterRule, UserFilterRule):
    """Check user's following count."""
    _keyword: ClassVar[str] = 'following'

    def __call__(self, user: User):
        return RuleResult(self, super().compare(user.following_count))


class ShortenFollowingUserFilterRule(UserFilterRule):
    _keyword: ClassVar[str] = 'following_more_than'

    @classmethod
    def parse_from_config(cls, conf: dict):
        return FollowingUserFilterRule(more_than=conf[cls._keyword])


class CreatedUserFilterRule(TemporalRangeFilterRule, UserFilterRule):
    """Check user (account) creating date."""
    _keyword: ClassVar[str] = 'created'

    def __call__(self, user: User):
        return RuleResult(self, super().compare(user.created_at))


class CreatedAfterUserFilterRule(UserFilterRule):
    _keyword: ClassVar[str] = 'created_after'

    @classmethod
    def parse_from_config(cls, conf: dict):
        return CreatedUserFilterRule(after=conf[cls._keyword])


class CreatedWithinDaysUserFilterRule(UserFilterRule):
    _keyword: ClassVar[str] = 'created_within_days'
    within_days: int

    @classmethod
    def parse_from_config(cls, conf: dict):
        return CreatedWithinDaysUserFilterRule(within_days=conf[cls._keyword])

    def __call__(self, user: User):
        edge = datetime.datetime.utcnow() - datetime.timedelta(days=self.within_days)
        return RuleResult(self, edge < user.created_at)


class TextMatchUserFilterRule(UserFilterRule):
    _keyword: ClassVar[str] = 'any_user_texts_match'
    pattern: re.Pattern

    @classmethod
    def parse_from_config(cls, conf: dict):
        return CreatedWithinDaysUserFilterRule(pattern=re.compile(conf[cls._keyword]))

    def __call__(self, user: User):
        return any(self.pattern.search(text) for text in
                   [user.name, user.description, user.pinned_tweet_text])
