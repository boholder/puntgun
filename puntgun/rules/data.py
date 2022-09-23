"""
DTOs of rule module
https://en.wikipedia.org/wiki/Data_transfer_object
"""
import sys
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Mapping, Optional

from pydantic import BaseModel, validator

from puntgun.rules.base import FromConfig

DEFAULT_TIME = datetime.utcnow()


def get_default_tweet_instance() -> "Tweet":
    return getattr(sys.modules[__name__], "Tweet")()


REF_HAVE_NOT_UPDATED = True


def update_user_class_ref() -> None:
    """
    Call this to let the "Tweet" class definition can be referred by "pinned_tweet" class attribute.
    """
    global REF_HAVE_NOT_UPDATED
    if REF_HAVE_NOT_UPDATED:
        User.update_forward_refs()
    REF_HAVE_NOT_UPDATED = False


class User(BaseModel):
    """
    https://developer.twitter.com/en/docs/twitter-api/data-dictionary/object-model/user
    https://developer.twitter.com/en/docs/twitter-api/users/lookup/api-reference/get-users-id
    """

    # Any field can be None in Twitter API response,
    # use "Optional" for avoiding this not-None pydantic validation error
    id: Optional[int] = 0
    name: Optional[str] = ""
    username: Optional[str] = ""
    profile_image_url: Optional[str] = ""
    created_at: Optional[datetime] = DEFAULT_TIME
    protected: Optional[bool] = False
    verified: Optional[bool] = False
    location: Optional[str] = ""
    description: Optional[str] = ""
    followers_count: Optional[int] = 0
    following_count: Optional[int] = 0
    tweet_count: Optional[int] = 0
    pinned_tweet_id: Optional[int] = 0
    pinned_tweet_text: Optional[str] = ""
    # IMPROVE: Can not overcome the forward-declaring problem.
    # I would like to give this attribute a "Tweet()" default value if I can.
    pinned_tweet: Optional["Tweet"]
    entities: Optional[Dict[str, Any]] = {}
    url: Optional[str] = ""
    withheld: Optional[Dict[str, Any]] = {}

    @staticmethod
    def from_response(resp_data: Mapping, pinned_tweet: "Tweet" = None) -> "User":
        if not resp_data:
            return User()

        update_user_class_ref()
        if not pinned_tweet:
            pinned_tweet = get_default_tweet_instance()

        public_metrics = resp_data["public_metrics"] if ("public_metrics" in resp_data) else {}

        # Find the true user pinned url in "entities.url.urls[]" instead of using Twitter shorten url (t.co)
        shorten_url = resp_data.get("url")
        if shorten_url:
            urls: List[dict] = resp_data.get("entities").get("url").get("urls")
            # 1. tweepy.User (type of "resp_data") inherits "DataMapping" to gain the get() method,
            # but we still need to use attribute-assignment way to update the value,
            # and this makes the type hint of "resp_data" becomes "tweepy.User" (coupled with tweepy library).
            #
            # 2. This updating operation has side effect (changes the value).
            #
            # So we would better generate a new dictionary from the origin resp_data
            # and change this dictionary instead.
            resp_data = dict(resp_data)
            resp_data["url"] = next(filter(lambda u: u.get("url") == shorten_url, urls)).get("expanded_url")

        return User(
            **resp_data,
            followers_count=public_metrics.get("followers_count", 0),
            following_count=public_metrics.get("following_count", 0),
            tweet_count=public_metrics.get("tweet_count", 0),
            pinned_tweet_text=pinned_tweet.text,
            pinned_tweet=pinned_tweet
        )

    class Config:
        validate_assignment = True

    @validator("location")
    def set_location(cls, loc: str) -> str:
        # IMPROVE: Is there any way to simplify these method?
        # Have tried dynamically adding decorated method with setattr(), do not work.
        #
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

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, type(self)):
            return self.id == other.id
        else:
            return False

    def __bool__(self) -> bool:
        return bool(self.id)


class Media(BaseModel):
    """https://developer.twitter.com/en/docs/twitter-api/data-dictionary/object-model/media"""

    media_key: Optional[str] = ""
    type: Optional[str] = ""
    url: Optional[str] = ""
    duration_ms: Optional[int] = 0
    height: Optional[int] = 0
    width: Optional[int] = 0
    alt_text: Optional[str] = ""
    preview_image_url: Optional[str] = ""
    public_metrics: Optional[dict] = {}
    variants: Optional[list] = []


class Poll(BaseModel):
    """https://developer.twitter.com/en/docs/twitter-api/data-dictionary/object-model/poll"""

    class Option(BaseModel):
        position: Optional[int] = 0
        label: Optional[str] = ""
        votes: Optional[int] = 0

    class Status(str, Enum):
        OPEN = "open"
        CLOSED = "closed"

    id: Optional[str] = ""
    options: Optional[List[Option]] = []
    duration_minutes: Optional[int] = 0
    end_datetime: Optional[datetime] = DEFAULT_TIME
    voting_status: Optional[Status] = Status.CLOSED


class Place(BaseModel):
    """https://developer.twitter.com/en/docs/twitter-api/data-dictionary/object-model/place"""

    id: Optional[str] = ""
    name: Optional[str] = ""
    full_name: Optional[str] = ""
    place_type: Optional[str] = ""
    # The identifiers of known place that contain the referenced place.
    # (Do not know what it is)
    contained_with: Optional[List[Any]] = []
    country: Optional[str] = ""
    country_code: Optional[str] = ""
    geo: Optional[dict] = {}


class ContextAnnotation(BaseModel):
    """
    It seems that Twitter use these annotations to tag tweet (text) content.
    One annotation includes two part, "domain" for explaining the category
    and "entity" for store the value.

    Depending on what is observed in the sampling,
    annotations may be repeated under the same tweet,
    and sometimes no description field exists in any two parts.
    """

    class Domain(BaseModel):
        id: Optional[str] = ""
        name: Optional[str] = ""
        description: Optional[str] = ""

    class Entity(BaseModel):
        id: Optional[str] = ""
        name: Optional[str] = ""
        description: Optional[str] = ""

    domain: Domain
    entity: Entity


class ReplySettings(str, Enum):
    EVERYONE = "everyone"
    MENTIONED_USERS = "mentionedUsers"
    FOLLOWING = "following"


class Tweet(BaseModel):
    """
    The field names aren't so straight like fields of User entity,
    so I pasted their descriptions from the official doc as comments.

    https://developer.twitter.com/en/docs/twitter-api/data-dictionary/object-model/tweet
    https://developer.twitter.com/en/docs/twitter-api/tweets/lookup/api-reference/get-tweets-id
    """

    id: Optional[int] = 0
    # Author's user information
    author: Optional[User] = User()
    created_at: Optional[datetime] = DEFAULT_TIME
    possibly_sensitive: Optional[bool] = False
    text: Optional[str] = ""
    retweet_count: Optional[int] = 0
    reply_count: Optional[int] = 0
    like_count: Optional[int] = 0
    quote_count: Optional[int] = 0
    reply_settings: Optional[ReplySettings] = ReplySettings.EVERYONE
    context_annotations: Optional[List[ContextAnnotation]] = []

    # Contains withholding details for withheld content
    # copyright, country_codes, scope
    withheld: Optional[Dict[str, Any]] = {}

    # The Tweet ID of the original Tweet of the conversation
    # (which includes direct replies, replies of replies)
    conversation_id: Optional[int] = 0

    # If this Tweet is a Reply, indicates the user ID of the parent Tweet's author.
    in_reply_to_user_id: Optional[int] = 0

    # A list of Tweets this Tweet refers to.
    # For example, if the parent Tweet is:
    # a Retweet, a Retweet with comment (also known as Quoted Tweet) or a Reply,
    # it will include the related Tweet referenced to by its parent.
    #
    # Example:
    # [{"type":<type (str)>,"id":<tweet id (int)>}...]
    #
    # Types have been found: "quoted" (quote tweet), "replied_to"
    referenced_tweets: Optional[List[Dict[str, Any]]] = []

    # Transform referenced_tweets into a convenient dictionary,
    # each key representing one type of reference.
    related_tweets: Optional[Dict[str, List["Tweet"]]] = {}

    # Application source
    # The name of the app the user Tweeted from
    source: Optional[str] = ""

    # Specifies the type of attachments (if any) present in this Tweet
    # media_keys (list), poll_ids (list)
    attachments: Optional[dict] = {}

    # Media attachments' information, such as video, photo...
    mediums: Optional[List[Media]] = []

    # Poll attachments' information
    polls: Optional[List[Poll]] = []

    # Contains details about the location tagged by the user in this Tweet,
    # if they specified one
    # IMPROVE: can not find a sample tweet that contains this "geo" field
    geo: Optional[Dict[str, Any]] = {}

    # got this from "response.includes.places" via "geo.place_id"
    place: Optional[Place] = Place()

    # Language of the Tweet, if detected by Twitter
    # Returned as a BCP47 language tag
    # https://en.wikipedia.org/wiki/IETF_language_tag
    # example: "en" (it's a subtag)
    # PS: pure emoji tweets' language is "art"
    lang: Optional[str] = ""

    # Contains details about text that has a special meaning in a Tweet
    # urls, hashtags, mentions, annotations (not the context annotation)...
    entities: Optional[Dict[str, Any]] = {}

    @staticmethod
    def from_response(
        resp_data: dict,
        author: User = None,
        mediums: List[Media] = None,
        polls: List[Poll] = None,
        place: Place = None,
        referenced_tweets: List["Tweet"] = None,
    ) -> "Tweet":
        """Other params except first one are data in 'response.includes' field that belong to this tweet"""
        if not resp_data:
            return Tweet()

        public_metrics = resp_data["public_metrics"] if ("public_metrics" in resp_data) else {}

        def corresponding_tweet(_id: str) -> "Tweet":
            return next(filter(lambda _t: _t.id == _id, referenced_tweets), Tweet())

        relations = {}
        if referenced_tweets:
            for t in resp_data["referenced_tweets"]:
                if t.get("type") not in relations:
                    relations[t.get("type")] = [corresponding_tweet(t.get("id"))]
                else:
                    relations[t.get("type")] += corresponding_tweet(t.get("id"))

        return Tweet(
            **resp_data,
            retweet_count=public_metrics.get("retweet_count", 0),
            reply_count=public_metrics.get("reply_count", 0),
            like_count=public_metrics.get("like_count", 0),
            quote_count=public_metrics.get("quote_count", 0),
            author=author,
            mediums=mediums,
            polls=polls,
            place=place,
            related_tweets=relations
        )

    class Config:
        validate_assignment = True

    @validator("in_reply_to_user_id")
    def set_reply_user_id(cls, uid: int) -> int:
        return uid or 0

    @validator("referenced_tweets")
    def set_ref_tweets(cls, tweets: list) -> list:
        return tweets or []

    @validator("source")
    def set_source(cls, src: str) -> str:
        return src or ""

    @validator("attachments")
    def set_attach(cls, attach: dict) -> dict:
        return attach or {}

    @validator("lang")
    def set_lang(cls, lang: str) -> str:
        return lang or ""

    @validator("geo")
    def set_geo(cls, geo: dict) -> dict:
        return geo or {}

    @validator("context_annotations")
    def set_ca(cls, ca: list) -> list:
        return ca or []

    @validator("entities")
    def set_entities(cls, ent: dict) -> dict:
        return ent or {}

    @validator("withheld")
    def set_withheld(cls, wh: dict) -> dict:
        return wh or {}


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
