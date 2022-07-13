from typing import List, Tuple, Callable, Any

import reactivex as rx
from reactivex import operators as op

from model.errors import TwitterApiError
from old.test.model.tweet import Tweet
from rules.user import User


class MixedResultProcessingWrapper(object):
    """
    In Current design, requesting on Hunter's method, i.e. on Twitter Dev API,
    will result in an observable mixing DTOs constructed from successful responses with request failure errors.

    Note that this type of error is business logic error (api error),
    corresponding to querying on single target (user, tweet...),
    which is recoverable, just record it and move to next target.
    While there is another type of error, client error,
    which is not recoverable and will stop the observable, same as regular "error" definition in Rx.

    We'll use the RxPY's group_by operator to separate these two types of results,
    decorating with input operators, and consuming with observers, declaratively.

    It is because of the inability to assign a value to the grouped observables
    and return them as return values that this class exists for processing grouped observables.
    """

    def __init__(self, result_observable: rx.Observable):
        self.observable = result_observable
        self.__error_observers = []
        self.__model_observers = []
        self.__error_operators = []
        self.__model_operators = []

    def pipe_on_model(self, *operators: Callable[[Any], Any]):
        self.__model_operators.extend(operators)
        return self

    def subscribe_on_model(self, *observers: rx.Observer):
        self.__model_observers.extend(observers)
        return self

    def pipe_on_error(self, *operators: Callable[[Any], Any]):
        self.__error_operators.extend(operators)
        return self

    def subscribe_on_error(self, *observers: rx.Observer):
        self.__error_observers.extend(observers)
        return self

    def wire(self):
        """
        Begin to actually consuming Twitter APIs response.
        (In Rx, the whole observable stream will be started
        once there are subscribers (observers) waiting for.)
        """

        def sub(grp: rx.GroupedObservable):
            src = grp.underlying_observable
            ops = self.__model_operators
            obs = self.__model_observers

            # check group_by predicate below —— errors will be put into True group
            if grp.key:
                ops = self.__error_operators
                obs = self.__error_observers

            after = src.pipe(*ops) if ops else src
            [after.subscribe(o) for o in obs]

        self.observable \
            .pipe(op.group_by(lambda x: isinstance(x, TwitterApiError))) \
            .subscribe(sub)

    def clean(self):
        self.__error_observers = []
        self.__error_operators = []
        self.__model_observers = []
        self.__model_operators = []


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
            -> MixedResultProcessingWrapper:
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
