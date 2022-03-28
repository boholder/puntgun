from datetime import datetime
from typing import List


class User:
    """
    DTO, one instance represent one user's basic information.

    The attributes are a subset of the fields in the Twitter user info query API response,
    I only pick those can be used as judgment metrics.
    You can easily guess the meaning of the attributes by their name.

    https://developer.twitter.com/en/docs/twitter-api/users/lookup/api-reference/get-users-id
    """

    def __init__(self,
                 uid: str = None,
                 name: str = None,
                 username: str = None,
                 profile_image_url: str = None,
                 created_at: datetime = None,
                 protected: bool = None,
                 verified: bool = None,
                 location: str = None,
                 description: str = None,
                 followers_count: int = None,
                 following_count: int = None,
                 tweet_count: int = None,
                 pinned_tweet_id: str = None,
                 pinned_tweet_text: str = None):
        self.id = uid
        self.name = name
        self.username = username
        self.profile_image_url = profile_image_url
        self.created_at = created_at
        self.protected = protected
        self.verified = verified
        self.location = location
        self.description = description
        self.followers_count = followers_count
        self.following_count = following_count
        self.tweet_count = tweet_count
        self.pinned_tweet_id = pinned_tweet_id
        self.pinned_tweet_text = pinned_tweet_text

    @staticmethod
    def build_from_response(response_data: dict, response_includes_tweets: list):
        # there may be no such user exist corresponding to the given id or username
        if not response_data:
            return User()

        public_metrics = response_data['public_metrics']
        # TODO 没pinned_tweet的情况？会返回空{}吗
        pinned_tweets_text: List[str] = [t["text"] for t in response_includes_tweets] \
            if response_includes_tweets else []

        return User(
            uid=response_data['id'],
            name=response_data['name'],
            username=response_data['username'],
            profile_image_url=response_data['profile_image_url'],
            created_at=response_data['created_at'],
            protected=response_data['protected'],
            verified=response_data['verified'],
            location=response_data['location'],
            description=response_data['description'],
            followers_count=public_metrics['followers_count'],
            following_count=public_metrics['following_count'],
            tweet_count=public_metrics['tweet_count'],
            pinned_tweet_id=response_data['pinned_tweet_id'],
            pinned_tweet_text='\n'.join(pinned_tweets_text))

    def __bool__(self):
        return self.id
