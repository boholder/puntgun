import functools
from typing import Any, Callable, Iterator, List

import tweepy
from loguru import logger
from tweepy import Response

from puntgun.conf import config, encrypto, secret
from puntgun.record import Record, Recordable, Recorder
from puntgun.rules.data import Tweet, User


class TwitterClientError(Exception):
    """Class for wrapping all Twitter client library custom errors."""

    def __init__(self) -> None:
        super().__init__("Twitter client raises unrecoverable error while querying Twitter API")


class TwitterApiError(Exception):
    """Corresponding to one https://developer.twitter.com/en/support/twitter-api/error-troubleshooting#partial-errors"""

    title = "generic twitter api error"

    def __init__(self, title: str, ref_url: str, detail: str, parameter: str, value: Any):
        super().__init__(f"{detail} Refer: {ref_url}")
        self.title = title
        self.ref_url = ref_url
        self.detail = detail
        self.parameter = parameter
        self.value = value

    @staticmethod
    def from_response(resp_error: dict) -> "TwitterApiError":
        # build an accurate error type according to the response content
        singleton_iter = (c for c in TwitterApiError.__subclasses__() if c.title == resp_error.get("title"))
        # if we haven't written a subclass for given error, return the generic error (in default value way)
        error_type = next(singleton_iter, TwitterApiError)

        return error_type(
            title=resp_error.get("title", ""),
            # when parsing from Twitter API response, key is 'type'
            # when parsing from :class:`Record` instance, key is 'ref_url'
            ref_url=resp_error.get("type", resp_error.get("ref_url", "")),
            detail=resp_error.get("detail", ""),
            parameter=resp_error.get("parameter", ""),
            value=resp_error.get("value", ""),
        )


class ResourceNotFoundError(TwitterApiError):
    """
    For example, if you try to query information about a not-exist user id,
    this error will be returned by Twitter server and raised by the tool.
    """

    title = "Not Found Error"


class TwitterApiErrors(Exception, Recordable):
    """
    This error is raised when a Twitter Dev API query returns http status code 200,
    but has an "errors" field in the response body,
    which indicates several "Partial error" occurs
    and the result only contains what Twitter server can figure out.

    https://developer.twitter.com/en/support/twitter-api/error-troubleshooting#partial-errors

    Corresponding to errors returned with one API query's response,
    contains a list of :class:`TwitterApiError`.
    """

    def __init__(self, query_func_name: str, query_params: dict, resp_errors: List[dict]):
        """Details for debugging via log."""
        self.query_func_name = query_func_name
        self.query_params = query_params
        self.errors = [TwitterApiError.from_response(e) for e in resp_errors]

        super().__init__(
            f"Twitter Server returned partial errors when querying API: "
            f"function called: {query_func_name}, "
            f"params: {query_params}, "
            f"errors: {self.errors}"
        )

    def __bool__(self) -> bool:
        return bool(self.errors)

    def __len__(self) -> int:
        return len(self.errors)

    def __iter__(self) -> Iterator[TwitterApiError]:
        return iter(self.errors)

    def __getitem__(self, index: int) -> TwitterApiError:
        return self.errors[index]

    def to_record(self) -> Record:
        return Record(
            type="twitter_api_errors",
            data={
                "query_func_name": self.query_func_name,
                "query_params": self.query_params,
                "errors": [e.__dict__ for e in self.errors],
            },
        )

    @staticmethod
    def parse_from_record(record: Record) -> "TwitterApiErrors":
        data = record.data
        return TwitterApiErrors(data.get("query_func_name", ""), data.get("query_params", ()), data.get("errors", []))


def record_twitter_api_errors(client_func: Callable[..., tweepy.Response]) -> Callable:
    """
    Decorator for recording Twitter API errors returned by tweepy or Twitter server
    while invoking :class:`tweepy.Client`.

    IMPROVE: It would be better if this function can act as a decorator on tweepy's client methods,
    or simplify this api-error-recording implement in another way.
    """

    def record_api_errors(request_params: dict, resp_errors: list) -> None:
        api_errors = TwitterApiErrors(client_func.__name__, request_params, resp_errors)
        logger.bind(o=True).info(api_errors)
        Recorder.record(api_errors)

    def decorator(*args: Any, **kwargs: Any) -> tweepy.Response:
        try:
            resp = client_func(*args, **kwargs)
            if hasattr(resp, "errors") and len(resp.errors) > 0:
                record_api_errors(kwargs, resp.errors)
            return resp
        except tweepy.errors.TweepyException as e:
            # We have no idea how to handle the error tweepy throws out.
            # just wrap it in a custom exception and let it fails the entire process.
            logger.exception("Client raises unrecoverable error while querying Twitter API")
            raise TwitterClientError from e

    return decorator


USER_API_FIELDS = [
    "id",
    "name",
    "username",
    "pinned_tweet_id",
    "profile_image_url",
    "created_at",
    "description",
    "public_metrics",
    "protected",
    "verified",
    "entities",
    "location",
    "url",
    "withheld",
]

# Not authorized to access 'non_public_metrics', 'organic_metrics', 'promoted_metrics'
# with free-registered Essential class token
TWEET_API_FIELDS = [
    "attachments",
    "author_id",
    "context_annotations",
    "conversation_id",
    "created_at",
    "entities",
    "geo",
    "id",
    "in_reply_to_user_id",
    "lang",
    "public_metrics",
    "possibly_sensitive",
    "referenced_tweets",
    "reply_settings",
    "source",
    "text",
    "withheld",
]

# Additional url params for querying Twitter user related api
# for letting the API know which fields we want to get.
USER_API_PARAMS = {
    "user_auth": True,
    "user_fields": USER_API_FIELDS,
    "tweet_fields": TWEET_API_FIELDS,
    "expansions": "pinned_tweet_id",
}

TWEET_API_PARAMS = {
    "user_auth": True,
    "user_fields": USER_API_FIELDS,
    "tweet_fields": TWEET_API_FIELDS,
    "expansions": [
        "attachments.poll_ids",
        "attachments.media_keys",
        "author_id",
        "entities.mentions.username",
        "geo.place_id",
        "in_reply_to_user_id",
        "referenced_tweets.id",
        "referenced_tweets.id.author_id",
    ],
    "media_fields": [
        "duration_ms",
        "height",
        "media_key",
        "preview_image_url",
        "type",
        "url",
        "width",
        "public_metrics",
        "alt_text",
        "variants",
    ],
    "place_fields": ["contained_within", "country", "country_code", "full_name", "geo", "id", "name", "place_type"],
    "poll_fields": ["duration_minutes", "end_datetime", "id", "options", "voting_status"],
}


class Client(object):
    """
    Adapter of :class:`tweepy.Client` for handling requests and responses to the Twitter API.

    Due to the rate limit set by the Twitter API,
    and tweepy will actively sleep and wait for the next attempt when hit the limit,
    the methods in this class are blocking.

    So here is the solution:
      1. One invocation on methods will send only **one** request to the Twitter API, makes the invocation "atomic".
      2. This class doesn't care about the terrible blocking, let the caller handle it.

    Ref:
      * https://developer.twitter.com/en/docs/twitter-api/rate-limits
      * It's so sweet that tweepy has inner retry logic for resumable 429 Too Many Request status code.
        https://github.com/tweepy/tweepy/blob/master/tweepy/client.py#L102-L114
    """

    def __init__(self, tweepy_client: tweepy.Client):
        # Add a decorator to record Twitter API errors in response
        # on every method of the tweepy client.
        for func_name in [method for method in dir(tweepy.Client) if not method.startswith("_")]:
            setattr(tweepy_client, func_name, record_twitter_api_errors(getattr(tweepy_client, func_name)))

        self.clt = tweepy_client
        # tweepy 4.10.0 changed return structure of tweepy.Client.get_me()
        # it's different from tweepy.Client.get_user()'s return structure
        # it's not the "data: [my_data]", but "data: my_data"
        self.me = User.from_response(self.clt.get_me().data)
        self.id = self.me.id
        self.name = self.me.name

    @staticmethod
    @functools.lru_cache(maxsize=1)
    def singleton() -> "Client":
        secrets = secret.load_or_request_all_secrets(encrypto.load_or_generate_private_key())
        return Client(
            tweepy.Client(
                consumer_key=secrets["ak"],
                consumer_secret=secrets["aks"],
                access_token=secrets["at"],
                access_token_secret=secrets["ats"],
            )
        )

    def get_users_by_usernames(self, names: List[str]) -> List[User]:
        """
        Query users information.
        **rate limit: 900 / 15 min**
        https://developer.twitter.com/en/docs/twitter-api/users/lookup/api-reference/get-users-by
        """
        if len(names) > 100:
            raise ValueError("at most 100 usernames per request")

        return response_to_users(self.clt.get_users(usernames=names, **USER_API_PARAMS))

    def get_users_by_ids(self, ids: List[int | str]) -> List[User]:
        """
        Query users information.
        **rate limit: 900 / 15 min**
        https://developer.twitter.com/en/docs/twitter-api/users/lookup/api-reference/get-users
        """
        if len(ids) > 100:
            raise ValueError("at most 100 user ids per request")

        return response_to_users(self.clt.get_users(ids=ids, **USER_API_PARAMS))

    def get_blocked(self) -> List[User]:
        """
        Get the latest blocking list of the current account.
        **rate limit: 15 / 15 min**
        https://developer.twitter.com/en/docs/twitter-api/users/blocks/api-reference/get-users-blocking
        """
        return query_paging_user_api(self.clt.get_blocked)

    @functools.lru_cache(maxsize=1)
    def cached_blocked(self) -> List[User]:
        """
        Call query method, cache them, and return the cache on latter calls.
        Since the tool may be constantly modifying the block list,
        this method just takes a snapshot of the list at the beginning,
        and it's sufficient for use.
        """
        return self.get_blocked()

    @functools.lru_cache(maxsize=1)
    def cached_blocked_id_list(self) -> List[int]:
        return [u.id for u in self.cached_blocked()]

    def get_following(self, user_id: int | str) -> List[User]:
        """
        Get the latest following list of a user.
        **rate limit: 15 / 15 min**
        https://developer.twitter.com/en/docs/twitter-api/users/follows/api-reference/get-users-id-following
        """
        return query_paging_user_api(self.clt.get_users_following, id=user_id)

    @functools.lru_cache(maxsize=1)
    def cached_following(self) -> List[User]:
        return self.get_following(self.id)

    @functools.lru_cache(maxsize=1)
    def cached_following_id_list(self) -> List[int]:
        return [u.id for u in self.cached_following()]

    def get_follower(self, user_id: int | str) -> List[User]:
        """
        Get the latest follower list of a user.
        **rate limit: 15 / 15 min**
        https://developer.twitter.com/en/docs/twitter-api/users/follows/api-reference/get-users-id-followers
        """
        return query_paging_user_api(self.clt.get_users_followers, id=user_id)

    @functools.lru_cache(maxsize=1)
    def cached_follower(self) -> List[User]:
        return self.get_follower(self.id)

    @functools.lru_cache(maxsize=1)
    def cached_follower_id_list(self) -> List[int]:
        return [u.id for u in self.cached_follower()]

    def block_user_by_id(self, target_user_id: int | str) -> bool:
        """
        Block given user on current account.
        **rate limit: 50 / 15 min**
        https://help.twitter.com/en/using-twitter/advanced-twitter-block-options
        https://developer.twitter.com/en/docs/twitter-api/users/blocks/api-reference/post-users-user_id-blocking
        """

        # this user has already been blocked
        if target_user_id in self.cached_blocked_id_list():
            logger.info(f"User[id={target_user_id}] has already been blocked.")
            return True

        # do not block your follower
        if (not config.settings.get("block_follower", True)) and target_user_id in self.cached_follower_id_list():
            logger.info(f"User[id={target_user_id}] is follower, not block base on config.")
            return False

        # do not block your following
        if (not config.settings.get("block_following", False)) and target_user_id in self.cached_following_id_list():
            logger.info(f"User[id={target_user_id}] is following, not block base on config.")
            return False

        # call the block api
        return self.clt.block(target_user_id=target_user_id).data["blocking"]

    def get_tweets_by_ids(self, ids: List[int | str]) -> List[Tweet]:
        """
        Query tweets information.
        **rate limit: 900 / 15 min**
        https://developer.twitter.com/en/docs/twitter-api/tweets/lookup/api-reference/get-tweets
        """
        if len(ids) > 100:
            raise ValueError("at most 100 tweet ids per request")

        return response_to_tweets(self.clt.get_tweets(ids=ids, **TWEET_API_PARAMS))


def response_to_users(resp: tweepy.Response) -> List[User]:
    """Build a list of :class:`User` instances from one response."""
    if not resp.data:
        return []

    pinned_tweets = [Tweet.from_response(d) for d in resp.includes.get("tweets", [])]

    def map_one(data: dict) -> User:
        """Build one user instance"""
        # find this user's pinned tweet
        pinned_tweet = next(filter(lambda t: t.id == data.get("pinned_tweet_id"), pinned_tweets), Tweet())
        return User.from_response(data, pinned_tweet)

    return [map_one(d) for d in resp.data]


def response_to_tweets(resp: tweepy.Response) -> List[Tweet]:
    """Build a list of :class:`Tweet` instances from one response."""
    if not resp.data:
        return []

    # get data in "includes" field
    # these items can be found by searching "includes." on official doc
    authors = [User.from_response(d) for d in resp.includes.get("users", [])]
    places = resp.includes.get("places", [])
    mediums = resp.includes.get("media", [])
    polls = resp.includes.get("polls", [])
    tweets = [Tweet.from_response(d) for d in resp.includes.get("tweets", [])]

    def map_one(data: dict) -> Tweet:
        """Build one tweet instance"""

        # IMPROVE: Each attribute's translating logic is slightly different from others,
        # so I can't reduce the code length by reusing a template function.
        author = next(filter(lambda u: u.id == data["author_id"], authors), User())

        if data["geo"] is not None:
            place: dict = next(filter(lambda p: p["place_id"] == data["geo"]["place_id"], places), {})
        else:
            place = {}

        attachments_data = data["attachments"] if data["attachments"] is not None else {}

        if "media_keys" in attachments_data:
            tweet_mediums = list(filter(lambda m: m["media_key"] in data["attachments"]["media_keys"], mediums))
        else:
            tweet_mediums = []

        if "poll_ids" in attachments_data:
            tweet_polls = list(filter(lambda p: p["id"] in data["attachments"]["poll_ids"], polls))
        else:
            tweet_polls = []

        if data["referenced_tweets"] is not None:
            referenced_tweet_ids = [t["id"] for t in data["referenced_tweets"]]
            referenced_tweets = list(filter(lambda t: t.id in referenced_tweet_ids, tweets))
        else:
            referenced_tweets = []

        return Tweet.from_response(data, author, tweet_mediums, tweet_polls, place, referenced_tweets)

    return [map_one(d) for d in resp.data]


def paging_api_iter(clt_func: Callable[..., Response], params: dict, pagination_token: str = None) -> tweepy.Response:
    """
    A recursion style generator that continue querying next page until hit the end.
    https://stackoverflow.com/questions/8991840/recursion-using-yield
    """
    response = clt_func(max_results=1000, pagination_token=pagination_token, **params)
    yield response

    # if is called again, query next page
    if hasattr(response, "meta") and "next_token" in response.meta:
        yield from paging_api_iter(clt_func, params, response.meta["next_token"])


def query_paging_user_api(clt_func: Callable[..., Response], **kwargs: Any) -> List[User]:
    # mix two part of params into one dict
    params = {}
    for k, v in USER_API_PARAMS.items():
        params[k] = v
    if kwargs:
        for k, v in kwargs.items():
            params[k] = v

    # use list() to query all pages
    responses = list(paging_api_iter(clt_func, params))
    # and return all users in responses as one list
    return functools.reduce(lambda a, b: a + b, [response_to_users(r) for r in responses], [])


class NeedClientMixin(object):
    """
    Some rules need a :class:`Client` to call for getting extra information.
    This class provides a lazy loading client field (call Client.singleton()).

    This class can also be used to label filter rules that take time to run their judgements
    (because they need to query Twitter API) and can't return immediately.
    """

    @property
    def client(self) -> Client:
        """
        Lazy load the client field to avoid:
        run unit test -> initialize this class -> call Client.singleton() -> require terminal input -> test fail
        https://github.com/samuelcolvin/pydantic/issues/1035#issuecomment-559043877

        Directly return the invocation for now, may complicate it for load balancing in the future.
        """
        return Client.singleton()
