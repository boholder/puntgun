from unittest.mock import MagicMock

from puntgun.rules.config_parser import ConfigParser
from puntgun.rules.data import User
from puntgun.rules.user.action_rules import BlockUserActionRule, UserActionRule


def test_block_user_action_rule(mock_client):
    mock_block_func = MagicMock(side_effect=[True, False])
    mock_client.block_user_by_id = mock_block_func

    rule = ConfigParser.parse({"block": {}}, UserActionRule)

    assert isinstance(rule, BlockUserActionRule)
    # first result is True
    assert bool(rule(User())) is True
    # second is False
    assert bool(rule(User())) is False
