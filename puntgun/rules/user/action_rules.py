from typing import ClassVar

from puntgun.client import NeedClient
from puntgun.rules import FromConfig, RuleResult
from puntgun.rules.user import User


class UserActionRule(FromConfig):
    """
    Takes **one** :class:`User` instance each time
    and perform an action (block, mute...) on this user via :class:`Client`.
    """

    def __call__(self, user: User) -> RuleResult:
        """
        Do operation on given user instance, and return the result (success or fail).
        Due to the operation takes time to perform (needs to call Twitter API),
        the result returned in reactivex :class:`Observable` type that contains only one boolean value.
        """


class BlockUserActionRule(UserActionRule, NeedClient):
    """
    Block the given user.
    TODO untested, no field in manual?
    """

    _keyword: ClassVar[str] = "block"

    def __call__(self, user: User) -> RuleResult:
        return RuleResult(self, self.client.block_user_by_id(user.id))

    @classmethod
    def parse_from_config(cls, conf: dict) -> "BlockUserActionRule":
        return BlockUserActionRule()
