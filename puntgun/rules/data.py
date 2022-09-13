"""
DTOs of rule module
https://en.wikipedia.org/wiki/Data_transfer_object
"""
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, validator
from rules import FromConfig

default_time = datetime.utcnow()


class User(BaseModel):
    """
    DTO, one instance represents one user(Twitter account)'s basic information.

    The attributes are a subset of the fields in the Twitter user info query API response,
    I only pick those can be used in judgment.
    You can easily guess the meaning of the attributes by their name.

    https://developer.twitter.com/en/docs/twitter-api/users/lookup/api-reference/get-users-id

    This class is highly affect by return values of :class:`tweepy.Client`.
    """

    # Any field can be None for avoiding validation error raising
    id: Optional[int] = 0
    name: Optional[str] = ""
    username: Optional[str] = ""
    profile_image_url: Optional[str] = ""
    created_at: Optional[datetime] = default_time
    protected: Optional[bool] = False
    verified: Optional[bool] = False
    location: Optional[str] = ""
    description: Optional[str] = ""
    followers_count: Optional[int] = 0
    following_count: Optional[int] = 0
    tweet_count: Optional[int] = 0
    pinned_tweet_id: Optional[int] = 0
    pinned_tweet_text: Optional[str] = ""
    entities: Optional[Dict[str, Any]] = {}
    url: Optional[str] = ""
    withheld: Optional[Dict[str, Any]] = {}

    class Config:
        validate_assignment = True

    @validator("location")
    def set_location(cls, loc: str) -> str:
        # When 'location' is provided but the value is None, set it to default value.
        return loc or ""

    @validator("pinned_tweet_id")
    def set_pinned_tweet_id(cls, tid: int) -> int:
        return tid or 0

    @validator("entities")
    def set_entities(cls, ent: dict) -> dict:
        return ent or {}

    @validator("url")
    def set_url(cls, url: dict) -> dict:
        return url or {}

    @validator("withheld")
    def set_withheld(cls, wh: dict) -> dict:
        return wh or {}

    @staticmethod
    def from_response(resp_data: dict, pinned_tweet_text: str) -> "User":
        # tweepy 4.10.0 changed return structure of tweepy.Client.get_me()
        # lacking most of the response field, helps enhancement of this constructor.

        # there may be no such user exist corresponding to the given id or username
        # in this case, the response.data = None
        if not resp_data:
            return User()

        # has this field and is not none
        public_metrics = resp_data["public_metrics"] if ("public_metrics" in resp_data) else {}

        return User(
            **resp_data,
            followers_count=public_metrics.get("followers_count", 0),
            following_count=public_metrics.get("following_count", 0),
            tweet_count=public_metrics.get("tweet_count", 0),
            pinned_tweet_text=pinned_tweet_text
        )

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, type(self)):
            return self.id == other.id
        else:
            return False

    def __bool__(self) -> bool:
        return bool(self.id)


class Tweet(BaseModel):
    # TODO unfinished
    pass


class RuleResult(object):
    """
    It's a special wrapper as filter/action rules' execution result.
    After a rule's execution, it returns an instance of this class instead of directly return the boolean value,
    zipping the rule instance itself with its boolean type filtering/operation result into one.

    It's for constructing execution report that need to tell
    WHICH filter rule is triggered or WHICH action rule is successfully executed.

    Rather than using tuple structure,
    we can simplify the logic by using bool(<result>) to get the boolean result
    (python will automatically do that for us)
    without extract/map the tuple before processing, so we can change lesser present code.
    """

    rule: FromConfig
    result: bool

    def __init__(self, rule: FromConfig, result: bool):
        self.rule = rule
        self.result = result

    def __bool__(self) -> bool:
        return self.result

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, type(self)):
            rule_equal = self.rule == other.rule
            result_equal = self.result == other.result
            return rule_equal and result_equal
        else:
            return False

    @staticmethod
    def true(rule: FromConfig) -> "RuleResult":
        return RuleResult(rule, True)

    @staticmethod
    def false(rule: FromConfig) -> "RuleResult":
        return RuleResult(rule, False)
