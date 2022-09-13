from typing import Any, Callable, ClassVar, List

import reactivex as rx
from loguru import logger
from reactivex import Observable
from reactivex import operators as op

from puntgun.client import NeedClientMixin
from puntgun.rules import FromConfig
from puntgun.rules.data import User


def handle_errors(func: Callable[..., rx.Observable]) -> Callable[..., rx.Observable]:
    def log_and_throw(e: Exception, _: Any) -> rx.Observable:
        logger.error("An exception is thrown from source rules and stops the pipeline.")
        return rx.throw(e)

    def wrapper(*args: Any, **kwargs: Any) -> rx.Observable:
        return func(*args, **kwargs).pipe(op.catch(log_and_throw))

    return wrapper


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

    @handle_errors
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

    @handle_errors
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
