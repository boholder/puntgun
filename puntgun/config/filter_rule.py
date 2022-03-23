from typing import Any

from puntgun.config.config_option import MapOption, Field, Option


class FilterRule(Option):
    """
    A filter rule's type can be any of Field, ListOption, MapOption,
    so let the subclasses choose their type and left this base class as a mere tag.
    """

    @classmethod
    def build(cls, config_value):
        """
        Let subclasses override this method by defining other base Option class
        ahead of this FilterRule class, so the subclasses will inherit the build method
        from other base Option class.
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


class SearchQueryFilterRule(Field, FilterRule):
    """
    Convenient :class:`SearchFilterRule` to search query,
    ``count`` default set to 100.
    """
    config_keyword = 'search-query'
    expect_type = str

    @classmethod
    def build(cls, config_value: Any):
        # Even not set ``count`` here,
        # it will be filled as 100 when SearchFilterRule building itself.
        # And after initializing, it will be treated as SearchFilterRule,
        # because we return a SearchFilterRule instance here.
        return SearchFilterRule.build({'query': config_value, 'count': 100})
