"""
Mainly testing Twitter APIs' response and tweepy's return values for development.
"""
from client import Client


def get_user_not_exist():
    # response.data = None
    response = Client.singleton().get_users_by_usernames(['9821hd91'])
    print(response)


def get_users():
    # includes.tweets: [] len 2
    response = Client.singleton().get_users_by_name(['TwitterDev', 'TwitterAPI'])
    print(response)


def get_user_without_pinned_tweet():
    # response includes: {} (no "tweets" field)
    # data.pinned_tweet_id: None
    response = Client.singleton().get_users_by_usernames(['Twitter'])
    print(response)


def get_users_focus_on_pinned_tweet_result():
    # includes.tweets: [] len 2, but no "Twitter"'s pinned tweet,
    # and this information doesn't show in response
    response = Client.singleton().get_users_by_usernames(['TwitterDev', 'Twitter', 'TwitterAPI'])
    print(response)


def block_user():
    # "@TwitterTV"
    response = Client.singleton().block_user_by_id(586198217)
    print(response)