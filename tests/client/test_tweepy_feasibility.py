from unittest import TestCase

from puntgun.client.tweepy_hunter import TweepyHunter


class TestTweepyUserApi(TestCase):
    """
    Mainly testing Twitter APIs' result for development.
    """

    client = TweepyHunter.singleton()

    # @unittest.skip("test for development")
    def test_get_user(self):
        response = self.client.get_user_by_name('9821hd91')
        print(response)

    # @unittest.skip("test for development")
    def test_get_users(self):
        # includes.tweets: [] len 2
        response = self.client.get_users_by_name(['TwitterDev', 'TwitterAPI'])
        print(response)

    # @unittest.skip("test for development")
    def test_get_user_without_pinned_tweet(self):
        # response includes: {} (no "tweets" field)
        # data.pinned_tweet_id: None
        response = self.client.get_user_by_name('Twitter')
        print(response)

    # @unittest.skip("test for development")
    def test_get_users_focus_on_pinned_tweet_result(self):
        # includes.tweets: [] len 2, but no "Twitter"'s pinned tweet,
        # and this information doesn't show in response
        response = self.client.get_users_by_name(['TwitterDev', 'Twitter', 'TwitterAPI'])
        print(response)
