"""
Mainly testing Twitter APIs' response and tweepy's return values for development.
"""

from puntgun.client import Client


def get_user_not_exist():
    # response.data = None
    response = Client.singleton().get_users_by_usernames(["9821hd91"])
    print(response)


def get_users():
    # includes.tweets: [] len 2
    response = Client.singleton().get_users_by_usernames(["TwitterDev", "TwitterAPI"])
    print(response)


def get_user_without_pinned_tweet():
    # response includes: {} (no "tweets" field)
    # data.pinned_tweet_id: None
    response = Client.singleton().get_users_by_usernames(["Twitter"])
    print(response)


def get_users_focus_on_pinned_tweet_result():
    # includes.tweets: [] len 2, but no "Twitter"'s pinned tweet,
    # and this information doesn't show in response
    response = Client.singleton().get_users_by_usernames(["TwitterDev", "Twitter", "TwitterAPI"])
    print(response)


def block_user():
    # "@TwitterTV"
    response = Client.singleton().block_user_by_id(586198217)
    print(response)


def get_blocking_list():
    users = Client.singleton().get_blocked()
    print(users)


def get_following_list():
    c = Client.singleton()
    users = c.get_following(c.id)
    print(users)


def get_follower_list():
    c = Client.singleton()
    users = c.get_follower(c.id)
    print(users)


def get_tweets():
    c = Client.singleton()
    # TwitterDev's tweet
    tweets = c.get_tweets_by_ids(
        [
            # media photo
            "1561805413103853570",
            # media video
            "1542891693044912128",
            # quote tweet
            "1562922967134539778",
            # poll (vote)
            "1571311257323708427",
            # reply
            "1559638635934371841",
            # directly retweet
            # (will not contain the info about user who did the retweet action)
            "1549477965381206017",
            # with geo
            # https://developer.twitter.com/en/docs/twitter-api/data-dictionary/object-model/place
            "1136048014974423040",
        ]
    )
    for t in tweets:
        print(t.json())

    print(tweets)


def get_liking_users_of_tweet():
    users = Client.singleton().get_users_who_like_tweet("1542891693044912128")
    print(users)


def get_retweet_tweet():
    users = Client.singleton().get_users_who_retweet_tweet("1542891693044912128")
    print(users)


get_tweets()
