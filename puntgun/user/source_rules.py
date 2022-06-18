from typing import List

from pydantic import BaseModel

from client import Client


class UserSourceRule(object):
    """
    Knows functions the :class:`puntgun.client.Client` provides.
    Queries the client with provided user information (in plan configuration),
    and returns a set of :class:`puntgun.model.user.User`.
    """


class NameUserSourceRule(BaseModel, UserSourceRule):
    """
    Queries Twitter client with provided usernames.
    The "username" is that "@foobar" one, Twitter calls it "handle".
    https://help.twitter.com/en/managing-your-account/change-twitter-handle
    """
    usernames: List[str]

    def __call__(self, clt: Client = Client.singleton()):
        return clt.get_users_by_usernames(self.usernames)
