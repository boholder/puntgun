from typing import Optional

from client import NeedClient
from rules import Rule
from rules.user import User


class UserActionRule(object):
    """
    Takes **one** :class:`User` instance each time
    and perform an action (block, mute...) on this user via :class:`Client`.
    """


class BlockUserActionRule(Rule, NeedClient, UserActionRule):
    """
    Block the given user.
    """

    keyword: Optional[str] = 'block'

    # TODO block_already_followed
    block_already_followed: bool = False

    def __call__(self, user: User):
        self.client.block_user_by_id(user.id)
