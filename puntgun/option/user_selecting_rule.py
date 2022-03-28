from typing import List, Dict, Any, Union, Tuple

import reactivex as rx
from reactivex import operators as op

from puntgun import util
from puntgun.base.options import Field, MapOption
from puntgun.model.errors import TwitterClientError, TwitterApiErrors
from puntgun.model.exchange import Exchange
from puntgun.model.user import User
from puntgun.option.let_me_check_rule import LetMeCheckRule
from puntgun.option.rule_set import RuleSet
from puntgun.spi.twitter_client.hunter import Hunter


class WhoField(Field):
    """
    Abstract class that represents the "who" field under UserSelectingRule.
    Has logic to retrieve indicate user group from Twitter client.
    """
    logger = util.get_logger(__qualname__)
    config_keyword = "who"
    required = True

    def query_users_from(self, client: Hunter) \
            -> rx.Observable[Union[User, TwitterApiErrors], TwitterClientError]:
        """Let child classes implement their various logic to query user from client."""
        raise NotImplementedError

    @classmethod
    @util.log_error_with(logger)
    def build(cls, config_value) -> 'WhoField':
        """Override the build method to return a WhoField instance."""
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

    def query_users_from(self, client: Hunter) \
            -> rx.Observable[Union[User, TwitterApiErrors], TwitterClientError]:
        return client.observe(user_ids=rx.of(self.user_ids))


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

    # attributes that will be set after initialization,
    # indicate their type for static type checking
    who: WhoField
    rules: RuleSet
    let_me_check_rule: LetMeCheckRule

    def __init__(self, config_value: Dict[str, Any]):
        super().__init__(config_value)

    def start(self, client: Hunter) \
            -> Tuple[rx.Observable[Exchange], rx.Observable[TwitterApiErrors]]:
        """
        Start user selecting rule.
        """

        def on_error(error: Exception):
            self.logger.error(f"UnError when querying user info with user ids from client", error)
            # can't handle, let this error fail whole program
            raise error

        # query users from client
        user_observe = self.who.query_users_from(client)
        user_observe.subscribe(on_error=on_error)

        exchange_observe = user_observe.pipe(
            op.filter(lambda x: isinstance(x, User)),
            op.map(lambda x: Exchange(user=x)))

        api_error_observe = user_observe.pipe(
            op.filter(lambda x: isinstance(x, TwitterApiErrors)))

        return exchange_observe, api_error_observe
