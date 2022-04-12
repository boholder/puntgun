import datetime
from abc import ABC
from datetime import datetime as dt
from typing import Any, Tuple, Dict

import reactivex as rx

from puntgun.base.options import MapOption, Field, Option
from puntgun.model.context import Context
from puntgun.model.errors import TwitterApiError


class FilterRule(Option, ABC):
    """
    Let the subclasses choose their type
    and left this base class as merely a tag.
    """


class ImmediateFilterRule(FilterRule, ABC):
    """
    A filter rule that can make judgment
    without querying other resource (which takes time).
    """

    def judge(self, context: Context) -> bool:
        """
        Check if given context triggers rule.
        """
        raise NotImplementedError


class DelayedFilterRule(FilterRule, ABC):
    """
    A filter rule that needs to make judgment
    with querying other resource (which takes time).
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

    config_keyword = 'search-query'
    expect_type = str

    @classmethod
    def build(cls, config_value: Any):
        # Even not set ``count`` here,
        # it will be filled as 100 when SearchFilterRule building itself.
        # And after initializing, it will be treated as SearchFilterRule,
        # because we return a SearchFilterRule instance here.
        return SearchFilterRule.build({'query': config_value, 'count': 100})


class UserCreatedFilterRule(MapOption, ImmediateFilterRule, FilterRule):
    """
    The rule for judging user's creation time.
    """
    config_keyword = 'user-created'
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
