import functools
import logging
from typing import List, Dict, Any

from puntgun.config.config_option import Field, MapOption
from puntgun.hunter import Hunter
from puntgun.util import log_error_with, get_instance_via_config


class WhoField(Field):
    """
    Abstract class that represents the "who" field under UserSelectingRule.
    Has logic to retrieve indicate user group from Twitter client.
    """
    logger = logging.getLogger(__name__)
    config_keyword = "who"

    def __init__(self, *args, **kwargs):
        super().__init__()

    def query_users_from_client(self):
        # TODO 从这里就要考虑响应式流上下文的格式了，作为返回值
        # TODO 按理说应该自己包装一个与单一user相关的上下文类，包含各种信息，可复用这些信息
        return self.query(Hunter.instance())

    def query(self, client: Hunter):
        """Let child classes implement their various logic to query user from client."""
        raise NotImplementedError

    @staticmethod
    @log_error_with(logger)
    def get_instance_via_config(raw_config_pair: Dict[str, Any]) -> 'WhoField':
        return get_instance_via_config(WhoField, raw_config_pair)

    @classmethod
    def build(cls, raw_config_value) -> 'WhoField':
        return cls.get_instance_via_config(raw_config_value)


class IdAreWhoField(WhoField):
    """
    "id-are" user selecting rule.
    """
    is_init_by_class_attr = True
    config_keyword = "id-are"
    expect_type = List[str]

    def __init__(self, raw_config_value: Any):
        super().__init__()
        self.user_ids = raw_config_value if raw_config_value else []

    @functools.lru_cache(maxsize=1)
    def query(self, client: Hunter):
        return 1


class UserSelectingRule(MapOption):
    """
    Model, a mapping of same name configuration option.
    """
    logger = logging.getLogger(__name__)
    config_keyword = 'users'
    valid_options = [WhoField]

    def __init__(self, raw_config_value: Dict[str, Any]):
        super().__init__(raw_config_value)
