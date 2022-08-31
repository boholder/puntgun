class Tweet(object):
    """
    DTO, one instance represent one existing tweet's information.

    The attributes are a subset of the fields in the Twitter user info query API response,
    I only pick those can be used as judgment metrics.
    You can easily guess the meaning of the attributes by their name.

    https://developer.twitter.com/en/docs/twitter-api/tweets/lookup/api-reference/get-tweets-id
    """
