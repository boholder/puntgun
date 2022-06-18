from unittest import TestCase

import conftest
from puntgun.client import Client


class TestTweepyUserApi(TestCase):
    """
    Mainly testing Twitter APIs' response and tweepy's return values for development.
    """

    @conftest.experimental
    def test_get_user_not_exist(self):
        # response.data = None
        response = Client.singleton().get_users_by_usernames(['9821hd91'])
        print(response)

    @conftest.experimental
    def test_get_users(self):
        # includes.tweets: [] len 2
        response = Client.singleton().get_users_by_name(['TwitterDev', 'TwitterAPI'])
        print(response)

    @conftest.experimental
    def test_get_user_without_pinned_tweet(self):
        # response includes: {} (no "tweets" field)
        # data.pinned_tweet_id: None
        response = Client.singleton().get_users_by_usernames(['Twitter'])
        print(response)

    @conftest.experimental
    def test_get_users_focus_on_pinned_tweet_result(self):
        # includes.tweets: [] len 2, but no "Twitter"'s pinned tweet,
        # and this information doesn't show in response
        response = Client.singleton().get_users_by_usernames(['TwitterDev', 'Twitter', 'TwitterAPI'])
        print(response)
