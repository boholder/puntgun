from typing import List, Dict, Any, Tuple

import reactivex as rx

import util
from puntgun.old.base.options import Field, MapOption
from puntgun.old.client.hunter import Hunter
from puntgun.old.model.decision import Decision
from puntgun.old.model.errors import TwitterApiError
from puntgun.old.model.user import User
from puntgun.old.option.let_me_check_rule import LetMeCheckRule
from puntgun.old.option.rule_set import RuleSet


class WhoField(Field):
    """
    Abstract class that represents the "who" field under UserSelectingRule.
    Has logic to retrieve indicate user group from Twitter client.
    """
    logger = util.get_logger(__qualname__)
    config_keyword = "who"
    required = True

    def query_users_from(self, client: Hunter) \
            -> Tuple[rx.Observable[User], rx.Observable[TwitterApiError]]:
        """Let child classes implement their various logic to query user from client."""
        raise NotImplementedError

    @classmethod
    @util.log_error_with(logger)
    def build(cls, config_value) -> 'WhoField':
        """Override the build method to return a WhoField instance."""
        return util.get_instance_via_config(WhoField, config_value)


class IdAreWhoField(WhoField):
    """
    "id_are" user selecting option.
    """
    is_init_by_class_attr = True
    config_keyword = "id_are"
    expect_type = List[str]

    def __init__(self, config_value: Any):
        super().__init__()
        self.user_ids = config_value if config_value else []

    def query_users_from(self, client: Hunter):
        return client.observe(user_ids=self.user_ids)


class UserSelectingRule(MapOption):

    logger = util.get_logger(__qualname__)
    config_keyword = 'users'
    # WhoField is special, we indicate the base class is valid option,
    # because we need to extract the real value from one-more-layer structure.
    # {'who': {'id_are': [1, 2, 3]}}
    valid_options = [WhoField, RuleSet, LetMeCheckRule]

    # attributes that will be set after initialization,
    # indicate their type for static type checking
    who: WhoField
    rules: RuleSet
    let_me_check_rule: LetMeCheckRule

    def __init__(self,
                 config_value: Dict[str, Any]):
        super().__init__(config_value)

    def start(self, client: Hunter) \
            -> Tuple[rx.Observable[Decision], rx.Observable[TwitterApiError]]:
        """
        Start user selecting rule.
        """

        # query users from client
        # users, errors = self.who.query_users_from(client)
