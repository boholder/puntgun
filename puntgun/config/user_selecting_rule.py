import functools
import logging
from typing import List, Dict, Any

from puntgun import util
from puntgun.config.config_option import Field, MapOption
from puntgun.config.let_me_check_rule import LetMeCheckRule
from puntgun.config.rule_set import RuleSet
from puntgun.hunter import Hunter


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

    def query_users_from_client(self):
        # TODO 从这里就要考虑响应式流上下文的格式了，作为返回值
        # TODO 按理说应该自己包装一个与单一user相关的上下文类，包含各种信息，可复用这些信息
        return self.query(Hunter.instance())

    def query(self, client: Hunter):
        """Let child classes implement their various logic to query user from client."""
        raise NotImplementedError

    @classmethod
    @util.log_error_with(logger)
    def build(cls, config_value) -> 'WhoField':
        return util.get_instance_via_config(WhoField, config_value)


class IdAreWhoField(WhoField):
    """
    "id-are" user selecting rule.
    """
    is_init_by_class_attr = True
    config_keyword = "id-are"
    expect_type = List[str]

    def __init__(self, config_value: Any):
        super().__init__()
        self.user_ids = config_value if config_value else []

    @functools.lru_cache(maxsize=1)
    def query(self, client: Hunter):
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
    valid_options = [WhoField, *RuleSet.__subclasses__(), *LetMeCheckRule.__subclasses__()]

    def __init__(self, config_value: Dict[str, Any]):
        super().__init__(config_value)
