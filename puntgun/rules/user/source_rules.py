from typing import List, ClassVar

import reactivex as rx
from loguru import logger
from reactivex import operators as ops, Observable

from client import NeedClient
from rules import FromConfig, SourceRule
from rules.user import User


def handle_errors(func):
    def log_and_throw(e, _):
        logger.error("An exception is thrown from source rules and stops the pipeline.")
        return rx.throw(e)

    def wrapper(*args, **kwargs):
        return func(*args, **kwargs).pipe(ops.catch(log_and_throw))

    return wrapper


class UserSourceRule(SourceRule):
    """
    Knows methods the :class:`Client` provides and how to get users information via these methods.
    Handling client's blocking behavior with :class:`reactivex` library.

    Queries the client with provided partial user information (from plan configuration),
    and returns an :class:`reactivex.Observable` of :class:`user.User`.
    """


class NameUserSourceRule(FromConfig, NeedClient, UserSourceRule):
    """
    Queries Twitter client with provided usernames.
    The "username" is that "@foobar" one, Twitter calls it "handle".
    https://help.twitter.com/en/managing-your-account/change-twitter-handle
    """
    _keyword: ClassVar[str] = 'names'
    names: List[str]

    @handle_errors
    def __call__(self) -> Observable[User]:
        return rx.from_iterable(self.names).pipe(
            # Some Twitter API limits the number of usernames
            # in a single request up to 100 like this one.
            # At least we needn't query one by one.
            ops.buffer_with_count(100),
            ops.map(self.client.get_users_by_usernames),
            ops.flat_map(lambda x: x),
        )

    @classmethod
    def parse_from_config(cls, conf: dict):
        """the config is { 'names': [...] } """
        return cls.parse_obj(conf)


class IdUserSourceRule(FromConfig, NeedClient, UserSourceRule):
    """
    Queries Twitter client with provided user IDs.
    You can find someone's user id when logining to Twitter
    via browser and check the XHRs with browser dev tool.
    """
    _keyword: ClassVar[str] = 'ids'
    ids: List[int | str]

    @handle_errors
    def __call__(self) -> Observable[User]:
        return rx.from_iterable(self.ids).pipe(
            # this api also allows to query 100 users at once.
            ops.buffer_with_count(100),
            ops.map(self.client.get_users_by_ids),
            ops.flat_map(lambda x: x),
        )

    @classmethod
    def parse_from_config(cls, conf: dict):
        return cls.parse_obj(conf)
