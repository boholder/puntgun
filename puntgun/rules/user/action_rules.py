import abc
from typing import ClassVar

from client import NeedClient
from rules import FromConfig
from rules.user import User


class UserActionRule(abc.ABC):
    """
    Takes **one** :class:`User` instance each time
    and perform an action (block, mute...) on this user via :class:`Client`.
    """


class BlockUserActionRule(FromConfig, NeedClient, UserActionRule):
    """
    Block the given user.
    """

    _keyword: ClassVar[str] = 'block'

    # TODO block_already_followed
    block_already_followed: bool = False

    def __call__(self, user: User):
        self.client.block_user_by_id(user.id)
