from typing import List

from pydantic import BaseModel

from client import Client


class UserSourceRule(object):
    """
    Knows methods the :class:`Client` provides and how to get users information via these methods.
    Handling client's blocking behavior with :class:`reactivex` library.
    Queries the client with provided partial user information (in plan configuration),
    and returns an :class:`reactivex.Observable` of :class:`user.User`.
    """


class NameUserSourceRule(BaseModel, UserSourceRule):
    """
    Queries Twitter client with provided usernames.
    The "username" is that "@foobar" one, Twitter calls it "handle".
    https://help.twitter.com/en/managing-your-account/change-twitter-handle
    """
    names: List[str]

    def __call__(self, clt: Client = Client.singleton()):
        return clt.get_users_by_usernames(self.names)


def split_to_one_hundred(lst: list):
    """
    Some Twitter API limits the number of usernames in a single request up to 100,
    at least we needn't query one by one.
    """
    for i in range(0, len(lst), 100):
        yield lst[i:i + 100]
