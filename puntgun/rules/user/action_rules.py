from typing import ClassVar

import reactivex as rx
from reactivex import Observable

from client import NeedClient
from rules import FromConfig, RuleResult
from rules.user import User


class UserActionRule(FromConfig):
    """
    Takes **one** :class:`User` instance each time
    and perform an action (block, mute...) on this user via :class:`Client`.
    """

    def __call__(self, user: User) -> Observable[RuleResult]:
        """
        Do operation on given user instance, and return the result (success or fail).
        Due to the operation takes time to perform (needs to call Twitter API),
        the result returned in reactivex :class:`Observable` type that contains only one boolean value.
        """


class BlockUserActionRule(UserActionRule, NeedClient):
    """
    Block the given user.
    """

    _keyword: ClassVar[str] = 'block'

    # TODO block_already_followed
    block_already_followed: bool = False

    def __call__(self, user: User):
        return rx.just(RuleResult(self, self.client.block_user_by_id(user.id)))
