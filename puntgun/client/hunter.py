from typing import List, Union, Tuple

import reactivex as rx
from tweepy import Tweet

from puntgun.model.errors import TwitterApiError
from puntgun.model.user import User


class Hunter(object):
    """
    Proxy interface of python Twitter client libraries (only "tweepy" currently).
    Initialing a Twitter client under one specific Twitter account's
    (which is this script's user's Twitter account) authorization.
    Provides methods for querying Twitter Dev API.
    """

    # The Twitter id of the authorized user used by the client,
    # for querying information about this user.
    id = None
    # And that user's name (besides the avatar), for logging purpose.
    name = None

    @staticmethod
    def singleton() -> 'Hunter':
        """Get singleton instance of Client."""
        raise NotImplementedError

    def observe(self,
                user_id: rx.Observable[str] = None,
                username: rx.Observable[str] = None,
                usernames: rx.Observable[List[str]] = None,
                user_ids: rx.Observable[str] = None) \
            -> Tuple[rx.Observable[User], rx.Observable[TwitterApiError]]:
        """Given user id(s) or username(s), get user(s) information via Twitter Dev API.

        :return: two streams:
            1. a stream of user(s) information, may be stopped by client error.
            2. a stream of Twitter API errors, tells which user(s) information failed to get.
        """
        raise NotImplementedError

    def find_feeding_place(self, user_id='') -> List[Tweet]:
        """Get user liked tweets via Twitter Dev API."""
        raise NotImplementedError

    def listen_tweeting(self, **params) -> List[Tweet]:
        """Search for tweets via Twitter Dev API."""
        raise NotImplementedError

    def shot_down(self, user_id='', user_ids=None) -> Union[bool, List[bool]]:
        """Block user via Twitter Dev API."""
        raise NotImplementedError

    def ignore(self, user_id='', user_ids=None) -> Union[bool, List[bool]]:
        """Mute user via Twitter Dev API."""
        raise NotImplementedError

    def check_decoy(self, count=1) -> List[User]:
        """Get your followers ids via Twitter Dev API."""
        raise NotImplementedError
