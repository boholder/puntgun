import itertools
from typing import ClassVar

import reactivex as rx
from loguru import logger
from reactivex import Observable
from reactivex import operators as op

from puntgun.client import NeedClientMixin
from puntgun.rules.base import FromConfig, validate_fields_conflict
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
    names: list[str]

    def __call__(self) -> rx.Observable[User]:
        return rx.from_iterable(self.names).pipe(
            # Some Twitter API limits the number of usernames
            # in a single request up to 100 like this one.
            # At least we needn't query one by one.
            op.buffer_with_count(100),
            # log for debug
            op.do(rx.Observer(on_next=lambda users: logger.debug("Batch of usernames to client: {}", users))),
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
    ids: list[int | str]

    def __call__(self) -> rx.Observable[User]:
        return rx.from_iterable(self.ids).pipe(
            # this api also allows to query 100 users at once.
            op.buffer_with_count(100),
            op.do(rx.Observer(on_next=lambda ids: logger.debug("Batch of user ids to client: {}", ids))),
            op.map(self.client.get_users_by_ids),
            op.flat_map(lambda x: x),
            op.do(rx.Observer(on_next=lambda u: logger.debug("User from client: {}", u))),
        )

    @classmethod
    def parse_from_config(cls, conf: dict) -> "IdUserSourceRule":
        return cls.parse_obj(conf)


class MyFollowerUserSourceRule(UserSourceRule, NeedClientMixin):
    """Take users from current account's followers."""

    _keyword = "my_followers"
    # last (newest) N followers
    last: int | None
    # first (oldest) N followers
    first: int | None
    # new followers after someone (@username)
    after_user: str | None

    @classmethod
    def parse_from_config(cls, conf: dict) -> "FromConfig":
        fields = conf.get(cls._keyword)
        validate_fields_conflict(fields, [["last"], ["first"], ["after_user"]])
        return cls.parse_obj(fields)

    def __call__(self) -> rx.Observable[User]:
        followers = self.client.cached_follower()
        has_field_configured = self.last or self.first or self.after_user
        if has_field_configured:
            return rx.from_iterable(self._take_part_of_followers(followers))
        else:
            # if no field, return all followers
            return rx.from_iterable(followers)

    def _take_part_of_followers(self, followers: list[User]) -> list[User]:
        if self.last:
            # the follower API response puts newer followers on list head.
            return followers[: self.last]
        elif self.first:
            return followers[-self.first :]
        else:
            # find given follower
            peak = next(filter(lambda u: u.username == self.after_user, followers), None)
            if peak is None:
                logger.warning(
                    "Could not find given follower username [{}] in current followers, "
                    "will skip this follower user source rule.",
                    self.after_user,
                )
                return []
            else:
                return list(itertools.takewhile(lambda u: u.id != peak.id, followers))
