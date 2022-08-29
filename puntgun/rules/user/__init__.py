from datetime import datetime
from typing import Optional

from pydantic import BaseModel, validator

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
    name: Optional[str] = ''
    username: Optional[str] = ''
    profile_image_url: Optional[str] = ''
    created_at: Optional[datetime] = default_time
    protected: Optional[bool] = False
    verified: Optional[bool] = False
    location: Optional[str] = ''
    description: Optional[str] = ''
    followers_count: Optional[int] = 0
    following_count: Optional[int] = 0
    tweet_count: Optional[int] = 0
    pinned_tweet_id: Optional[int] = 0
    pinned_tweet_text: Optional[str] = ''
    entities: Optional[dict] = {}
    url: Optional[str] = ''
    withheld: Optional[dict] = {}

    class Config:
        validate_assignment = True

    @validator('location')
    def set_location(cls, loc):
        # When 'location' is provided but the value is None, set it to default value.
        return loc or ''

    @validator('pinned_tweet_id')
    def set_pinned_tweet_id(cls, tid):
        return tid or 0

    @validator('entities')
    def set_entities(cls, ent):
        return ent or {}

    @validator('url')
    def set_url(cls, url):
        return url or {}

    @validator('withheld')
    def set_withheld(cls, wh):
        return wh or {}

    @staticmethod
    def from_response(resp_data: dict, pinned_tweet_text: str):
        # tweepy 4.10.0 changed return structure of tweepy.Client.get_me()
        # lacking most of the response field, helps enhancement of this constructor.

        # there may be no such user exist corresponding to the given id or username
        # in this case, the response.data = None
        if not resp_data:
            return User()

        # has this field and is not none
        public_metrics = resp_data['public_metrics'] if ('public_metrics' in resp_data) else {}

        return User(**resp_data,
                    followers_count=public_metrics.get('followers_count', 0),
                    following_count=public_metrics.get('following_count', 0),
                    tweet_count=public_metrics.get('tweet_count', 0),
                    pinned_tweet_text=pinned_tweet_text)

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return self.id == other.id
        return False

    def __bool__(self):
        return bool(self.id)
