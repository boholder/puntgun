import datetime
import re
from abc import ABC
from datetime import datetime as dt
from typing import Any, Tuple, Dict

import reactivex as rx

from puntgun.base.options import MapOption, Field, Option
from puntgun.model.context import Context
from puntgun.model.errors import TwitterApiError


class FilterRule(Option, ABC):
    """
    Let the subclasses choose their type and left this base class as merely a tag.
    """
    # TODO 单个rule抛异常不应该影响其他rule，更不能断掉程序，抛个自定义RuleError
    # TODO 在解析plan(init)时rule抛异常，说明输入有问题，直接断掉程序。


class ImmediateFilterRule(FilterRule, ABC):
    """
    A filter rule that can make judgment without querying other resource.
    """

    def judge(self, context: Context) -> bool:
        """
        Check if given context triggers rule.
        """
        raise NotImplementedError


class DelayedFilterRule(FilterRule, ABC):
    """
    A filter rule that needs to make judgment with querying other resource (which takes time).
    """

    def judge(self, context: Context) -> Tuple[bool, TwitterApiError]:
        """
        Check if given context triggers rule.
        """
        raise NotImplementedError


class SearchFilterRule(MapOption, DelayedFilterRule, FilterRule):
    """
    Perform a tweet search with given parameters on potential user.
    Triggered if search result of potential user isn't empty.
    """

    config_keyword = 'search'
    valid_options = [Field.of('name', str),
                     Field.of('count', int, default_value=100),
                     Field.of('query', str, required=True)]

    def judge(self, context: Context) -> Tuple[bool, TwitterApiError]:
        """"""
        pass


class SearchQueryFilterRule(Field, DelayedFilterRule, FilterRule):
    """
    Convenient :class:`SearchFilterRule` to search query,
    ``count`` default set to 100.
    """

    def judge(self, context: Context) -> Tuple[rx.Observable[bool], rx.Observable[TwitterApiError]]:
        """"""
        raise NotImplementedError

    config_keyword = 'search_query'
    expect_type = str

    @classmethod
    def build(cls, config_value: Any):
        # Even not set ``count`` here,
        # it will be filled as 100 when SearchFilterRule building itself.
        # And after initializing, it will be treated as SearchFilterRule,
        # because we return a SearchFilterRule instance here.
        return SearchFilterRule.build({'query': config_value, 'count': 100})


class TimeComparingFilterRule(MapOption, ImmediateFilterRule):
    valid_options = [Field.of('before', str, default_value=dt.utcnow().strftime('%Y-%m-%d')),
                     Field.of('after', str, default_value='2000-01-01'),
                     Field.of('within_days', int, conflict_with=['before', 'after'])]

    def __init__(self, config_value: Dict[str, Any]):
        super().__init__(config_value)

        # if no 'within_days' field,
        # convert input time string to datetime format
        if not hasattr(self, 'within_days'):
            self.before = dt.fromisoformat(self.before)
            self.after = dt.fromisoformat(self.after)

            assert self.before >= self.after, \
                f'Option [{self}]: "before" ({self.before}) should be after "after" ({self.after})'

    def judge(self, context: Context) -> bool:
        created_time = context.user.created_at

        if hasattr(self, 'within_days'):
            return dt.utcnow() - datetime.timedelta(days=self.within_days) <= created_time
        else:
            return self.after <= created_time <= self.before


class UserCreatedFilterRule(TimeComparingFilterRule, ImmediateFilterRule, FilterRule):
    """
    The rule for judging user's creation time.
    """
    config_keyword = 'user_created'


class UserCreatedAfterFilterRule(Field, ImmediateFilterRule, FilterRule):
    """Shorten version of UserCreatedFilterRule"""

    def judge(self, context: Context) -> bool:
        raise NotImplementedError

    config_keyword = 'user_created_after'
    expect_type = str

    @classmethod
    def build(cls, config_value: Any):
        return UserCreatedFilterRule.build({'after': config_value})


class UserCreatedWithinDaysFilterRule(Field, ImmediateFilterRule, FilterRule):
    """Shorten version of UserCreatedFilterRule"""

    def judge(self, context: Context) -> bool:
        raise NotImplementedError

    config_keyword = 'user_created_within_days'
    expect_type = int

    @classmethod
    def build(cls, config_value: Any):
        return UserCreatedFilterRule.build({'within_days': config_value})


class UserTextsMatchFilterRule(Field, ImmediateFilterRule, FilterRule):
    """
    The rule for judging user's text match.
    """
    config_keyword = 'user_texts_match'
    expect_type = str

    def __init__(self, config_value: str):
        super().__init__()
        self.regex = re.compile(config_value)

    @classmethod
    def build(cls, config_value: Any):
        """Override the Field class's build method."""
        return cls(super().build(config_value))

    def judge(self, context: Context) -> bool:
        return any(self.regex.search(text) for text in
                   [context.user.name, context.user.description, context.user.pinned_tweet_text])


class NumberComparingFilterRule(Field, ImmediateFilterRule):
    pass
