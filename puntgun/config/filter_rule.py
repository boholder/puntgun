from puntgun.config.config_option import MapOption, Field


class FilterRule(object):
    """
    A filter rule's type can be any of Field, ListOption, MapOption,
    so let the subclasses choose their type and left this base class as a mere tag.
    """


class NameField(Field):
    """
    A field that is used to indicate a custom name to a rule.
    """
    config_keyword = 'name'
    expect_type = str


class SearchFilterRule(MapOption, FilterRule):
    """
    Perform a tweet search with given parameters on potential user.
    Triggered if search result of potential user isn't empty.
    """
    config_keyword = 'search'
    valid_options = []
