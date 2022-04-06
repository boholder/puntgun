from typing import List, Tuple

import reactivex as rx

from puntgun.model.Tweet import Tweet
from puntgun.model.errors import TwitterApiError
from puntgun.model.user import User


class Hunter(object):
    """
    Proxy of python Twitter client libraries (only "tweepy" currently).

    * Initialing a Twitter client under one specific Twitter account's
      (which is this script's user's Twitter account) authorization.

    * Provides methods for querying Twitter Dev APIs.
    """

    # The Twitter user id of the authorized user used by the client.
    id: int
    # And that user's name (besides the avatar), for logging purpose.
    name: str
    # And other information about this user.
    me: User

    # Every query to Twitter API may respond with API errors,
    # that's why you can see almost every method of this class
    # returning normal result stream along with error stream.

    @staticmethod
    def singleton() -> 'Hunter':
        """Get singleton instance of Client."""
        raise NotImplementedError

    def observe(self,
                user_id: int = None,
                username: str = None,
                user_ids: List[int] = None,
                usernames: List[str] = None) \
            -> Tuple[rx.Observable[User], rx.Observable[TwitterApiError]]:
        """Given user id(s) or username(s), get user(s) information.

        :returns: two streams:
            1. a stream of user(s) information, may be stopped by client error.
            2. a stream of Twitter API errors, tell which user(s) information is(are) failed to get.
        """
        raise NotImplementedError

    def find_feeding_place(self, user_id: int) -> Tuple[rx.Observable[Tweet], rx.Observable[TwitterApiError]]:
        """Get user liked tweets."""
        raise NotImplementedError

    def listen_tweeting(self, **params) -> Tuple[rx.Observable[Tweet], rx.Observable[TwitterApiError]]:
        """Search for tweets."""
        raise NotImplementedError

    def shot_down(self, user_id: int) -> Tuple[rx.Observable[bool], rx.Observable[TwitterApiError]]:
        """Block single user."""
        raise NotImplementedError

    def group_by_shot_down(self, users: rx.Observable[User]) -> Tuple[rx.Observable[User], rx.Observable[User]]:
        """
        Group input users according to whether they have been blocked by you.
        :returns: two streams: blocked, not blocked.
        """
        raise NotImplementedError

    def check_decoy(self, recent: int) -> Tuple[rx.Observable[User], rx.Observable[TwitterApiError]]:
        """Get your followers' user ids."""
        raise NotImplementedError