from datetime import datetime


class User:
    """
    DTO, one instance represent one user's basic information.

    The attributes are a subset of the fields in the Twitter user info query API response,
    I only pick those can be used as judgment metrics.
    You can easily guess the meaning of the attributes by their name.

    https://developer.twitter.com/en/docs/twitter-api/users/lookup/api-reference/get-users-id
    """

    def __init__(self,
                 uid: int = None,
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
                 pinned_tweet_id: int = None,
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
    def build_from_response(resp_data: dict, pinned_tweet_text: str):
        # there may be no such user exist corresponding to the given id or username
        # in this case, the response.data = None
        if not resp_data:
            return User()

        public_metrics = resp_data['public_metrics']

        return User(
            uid=resp_data['id'],
            name=resp_data['name'],
            username=resp_data['username'],
            profile_image_url=resp_data['profile_image_url'],
            created_at=resp_data['created_at'],
            protected=resp_data['protected'],
            verified=resp_data['verified'],
            location=resp_data['location'],
            description=resp_data['description'],
            followers_count=public_metrics['followers_count'],
            following_count=public_metrics['following_count'],
            tweet_count=public_metrics['tweet_count'],
            pinned_tweet_id=resp_data['pinned_tweet_id'],
            pinned_tweet_text=pinned_tweet_text if pinned_tweet_text else '')

    def __bool__(self):
        return bool(self.id)
