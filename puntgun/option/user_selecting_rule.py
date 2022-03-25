from typing import List, Dict, Any

from puntgun import util
from puntgun.base.option import Field, MapOption
from puntgun.hunter import Hunter
from puntgun.option.let_me_check_rule import LetMeCheckRule
from puntgun.option.rule_set import RuleSet


class WhoField(Field):
    """
    Abstract class that represents the "who" field under UserSelectingRule.
    Has logic to retrieve indicate user group from Twitter client.
    """
    logger = util.get_logger(__qualname__)
    config_keyword = "who"
    required = True

    def __init__(self, *args, **kwargs):
        super().__init__()

    def query_users_from(self, client: Hunter):
        """Let child classes implement their various logic to query user from client."""
        raise NotImplementedError

    @classmethod
    @util.log_error_with(logger)
    def build(cls, config_value) -> 'WhoField':
        return util.get_instance_via_config(WhoField, config_value)


class IdAreWhoField(WhoField):
    """
    "id-are" user selecting option.
    """
    is_init_by_class_attr = True
    config_keyword = "id-are"
    expect_type = List[str]

    def __init__(self, config_value: Any):
        super().__init__()
        self.user_ids = config_value if config_value else []

    def query_users_from(self, client: Hunter):
        return 1


class UserSelectingRule(MapOption):
    """
    Model, a mapping of same name configuration option.
    """
    logger = util.get_logger(__qualname__)
    config_keyword = 'users'
    # WhoField is special, we indicate the base class is valid option,
    # because we need to extract the real value from one-more-layer structure.
    # {'who': {'id-are': [1, 2, 3]}}
    valid_options = [WhoField, RuleSet, LetMeCheckRule]

    def __init__(self, config_value: Dict[str, Any]):
        super().__init__(config_value)
