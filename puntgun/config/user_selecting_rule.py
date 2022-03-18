import functools
import logging
from typing import List, Dict, Any

from puntgun.config.config_option import Field, MapOption
from puntgun.hunter import Hunter
from puntgun.util import log_error_with


class WhoField(Field):
    """
    Abstract class that represents the "who" field under UserSelectingRule.
    Has logic to retrieve indicate user group from Twitter client.
    """
    logger = logging.getLogger(__name__)
    config_keyword = "who-field-generic"
    client = Hunter.instance()

    def __init__(self, raw_config_value: Any):
        super().__init__()
        self.check_expect_type_constraint(raw_config_value)
        self.set_value(raw_config_value)

    def query_users_from_client(self):
        # TODO 从这里就要考虑响应式流上下文的格式了，作为返回值
        # TODO 按理说应该自己包装一个与单一user相关的上下文类，包含各种信息，可复用这些信息
        """Let child classes implement their various logic to query user from client."""
        raise NotImplementedError

    def set_value(self, config_value: Any):
        """
        Child classes can set their value as different attribute name,
        cooperating with their unique ``__query`` method implement.
        """
        raise NotImplementedError

    @staticmethod
    @log_error_with(logger)
    def get_instance_via_config(raw_config_pair: Dict[str, Any]) -> 'WhoField':
        """Find same ``config_keyword`` in all WhoField subclasses
        and return the instance of matched subclass.

        :param raw_config_pair: e.g. {"id-are": ["1", "2"]}
        """
        keyword, value = raw_config_pair.popitem()
        for subclass in WhoField.__subclasses__():
            if subclass.config_keyword == keyword:
                return subclass(value)
        raise ValueError(f"No such who field matches [{keyword}], "
                         f"please fix it in your configuration.")


class IdAreWhoField(WhoField):
    """
    "id-are" field
    """
    is_init_by_class_attr = True
    config_keyword = "id-are"
    expect_type = List[str]

    def __init__(self, raw_config_value: Any):
        self.user_ids = None
        super().__init__(raw_config_value)

    @functools.lru_cache(maxsize=1)
    def query_users_from_client(self):
        return 1

    def set_value(self, raw_config_value):
        self.user_ids = raw_config_value if raw_config_value else []


class UserSelectingRule(MapOption):
    """
    Model, a mapping of same name configuration option.
    """
    logger = logging.getLogger(__name__)
    config_keyword = 'users'

    def __init__(self, raw_config_value: Dict[str, Any]):
        super().__init__(raw_config_value)
        self.who = WhoField.get_instance_via_config(raw_config_value.get("who"))
        # self.rule_set = rule_set
        # self.let_me_check = let_me_check

    def