from typing import ClassVar, List

import reactivex as rx
from loguru import logger
from reactivex import Observable
from reactivex import operators as op

from puntgun.client import NeedClientMixin
from puntgun.rules.base import FromConfig
from puntgun.rules.data import User


class UserSourceRule(FromConfig):
    """
    Knows methods the :class:`Client` provides and how to get users information via these methods.
    Handling client's blocking behavior with :class:`reactivex` library.

    Queries the client with provided partial user information (from plan configuration),
    and returns an :class:`reactivex.Observable` of :class:`user.User`.
    """

    def __call__(self) -> Observable[User]:
        """"""


class NameUserSourceRule(UserSourceRule, NeedClientMixin):
    """
    Queries Twitter client with provided usernames.
    The "username" is that "@foobar" one, Twitter calls it "handle".
    https://help.twitter.com/en/managing-your-account/change-twitter-handle
    """

    _keyword: ClassVar[str] = "names"
    names: List[str]

    def __call__(self) -> rx.Observable:
        return rx.from_iterable(self.names).pipe(
            # Some Twitter API limits the number of usernames
            # in a single request up to 100 like this one.
            # At least we needn't query one by one.
            op.buffer_with_count(100),
            # log for debug
            op.do(rx.Observer(on_next=lambda users: logger.debug("Buffered user names: {}", users))),
            op.map(self.client.get_users_by_usernames),
            op.flat_map(lambda x: x),
            op.do(rx.Observer(on_next=lambda u: logger.debug("User from client: {}", u))),
        )

    @classmethod
    def parse_from_config(cls, conf: dict) -> "NameUserSourceRule":
        """the config is { 'names': [...] }"""
        return cls.parse_obj(conf)


class IdUserSourceRule(UserSourceRule, NeedClientMixin):
    """
    Queries Twitter client with provided user IDs.
    You can find someone's user id when logining to Twitter
    via browser and check the XHRs with browser dev tool.
    """

    _keyword: ClassVar[str] = "ids"
    ids: List[int | str]

    def __call__(self) -> rx.Observable:
        return rx.from_iterable(self.ids).pipe(
            # this api also allows to query 100 users at once.
            op.buffer_with_count(100),
            op.map(self.client.get_users_by_ids),
            op.flat_map(lambda x: x),
        )

    @classmethod
    def parse_from_config(cls, conf: dict) -> "IdUserSourceRule":
        return cls.parse_obj(conf)


class MyFollowerUserSourceRule(UserSourceRule, NeedClientMixin):
    """Take users from current account's followers."""

    _keyword = "my_follower"
    # last (newest) N followers
    last: int
    #
    before: str

    def __call__(self) -> rx.Observable:
        pass
