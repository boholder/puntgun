import asyncio
from abc import ABC
from typing import Any, Tuple

import reactivex as rx

from puntgun.base.options import MapOption, Field, Option
from puntgun.model.context import Context
from puntgun.model.errors import TwitterApiError


class FilterRule(Option, ABC):
    """
    A filter option's type can be any of Field, ListOption, MapOption,
    so let the subclasses choose their type
    and left this base class as merely a tag.
    """

    def judge(self, context: rx.Observable[Context]) \
            -> rx.Observable[asyncio.Future[bool]]:
        """
        Check if given context triggers rule.

        Since 1. checking process may need to acquire some extra resources vai API,
        2. some type of RuleSet will cancel this process
        if other brother rules (rules under same RuleSet) return their result earlier.
        The process's controlling is wrapped in Future type.
        """
        raise NotImplementedError


class SearchFilterRule(MapOption, FilterRule):
    """
    Perform a tweet search with given parameters on potential user.
    Triggered if search result of potential user isn't empty.
    """

    config_keyword = 'search'
    valid_options = [Field.of('name', str),
                     Field.of('count', int, default_value=100),
                     Field.of('query', str, required=True)]

    def judge(self, context: Context) \
            -> Tuple[rx.Observable[bool], rx.Observable[TwitterApiError]]:
        pass


class SearchQueryFilterRule(Field, FilterRule):
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
