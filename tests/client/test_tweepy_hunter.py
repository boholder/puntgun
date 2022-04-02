from datetime import datetime
from unittest import TestCase
from unittest.mock import Mock, MagicMock

import reactivex as rx
import tweepy
from hamcrest import assert_that, is_

from puntgun.client.tweepy_hunter import TweepyHunter
from puntgun.model.errors import ResourceNotFoundError
from puntgun.model.user import User


class TestTweepyHunter(TestCase):
    """
    Test the TweepyHunter class while mocking the tweepy API.
    """

    create_time = datetime.now()
    image_url = 'https://example.com'

    # these three test data based on real response of Twitter API
    normal_user_response = tweepy.Response(data=[{'id': 1, 'name': 'Test User', 'username': 'TestUser',
                                                  'pinned_tweet_id': 1, 'profile_image_url': image_url,
                                                  'created_at': create_time,
                                                  'description': 'hi',
                                                  'location': None,
                                                  'public_metrics': {'followers_count': 1,
                                                                     'following_count': 2,
                                                                     'tweet_count': 3,
                                                                     'listed_count': 4},
                                                  'protected': False, 'verified': True}],
                                           includes={'tweets': [{'id': 1, 'text': 'pinned tweet'}]},
                                           meta={}, errors=[])

    no_pinned_tweet_user_response = tweepy.Response(data=[{'id': 2, 'name': 'No Pinned Tweet User',
                                                           'username': 'NoPinnedTweetUser',
                                                           'pinned_tweet_id': None,
                                                           'profile_image_url': image_url,
                                                           'created_at': create_time,
                                                           'description': 'hi',
                                                           'location': None,
                                                           'public_metrics': {'followers_count': 1,
                                                                              'following_count': 2,
                                                                              'tweet_count': 3,
                                                                              'listed_count': 4},
                                                           'protected': False, 'verified': False}],
                                                    errors=[], includes={}, meta={})

    not_exist_user_response = tweepy.Response(data=None, includes={}, meta={},
                                              errors=[{'value': 'ErrorUser',
                                                       'detail': 'Could not find user with username: [ErrorUser].',
                                                       'title': 'Not Found Error', 'resource_type': 'user',
                                                       'parameter': 'username',
                                                       'resource_id': 'ErrorUser',
                                                       'type': 'https://api.twitter.com/2/problems/resource-not-found'}]
                                              )

    @staticmethod
    def assert_normal_user(user: User):
        assert_that(user.id, is_(1))
        assert_that(user.name, is_('Test User'))
        assert_that(user.username, is_('TestUser'))
        assert_that(user.pinned_tweet_id, is_(1))
        assert_that(user.profile_image_url, is_(TestTweepyHunter.image_url))
        assert_that(user.created_at, is_(TestTweepyHunter.create_time))
        assert_that(user.description, is_('hi'))
        assert_that(user.location, is_(None))
        assert_that(user.followers_count, is_(1))
        assert_that(user.following_count, is_(2))
        assert_that(user.tweet_count, is_(3))
        assert_that(user.protected, is_(False))
        assert_that(user.verified, is_(True))
        assert_that(user.pinned_tweet_text, is_('pinned tweet'))

    @staticmethod
    def assert_no_pinned_tweet_user(user: User):
        assert_that(user.id, is_(2))
        assert_that(user.name, is_('No Pinned Tweet User'))
        assert_that(user.username, is_('NoPinnedTweetUser'))
        assert_that(user.pinned_tweet_id, is_(None))
        assert_that(user.profile_image_url, is_(TestTweepyHunter.image_url))
        assert_that(user.created_at, is_(TestTweepyHunter.create_time))
        assert_that(user.description, is_('hi'))
        assert_that(user.location, is_(None))
        assert_that(user.followers_count, is_(1))
        assert_that(user.following_count, is_(2))
        assert_that(user.tweet_count, is_(3))
        assert_that(user.protected, is_(False))
        assert_that(user.verified, is_(False))
        assert_that(user.pinned_tweet_text, is_(''))

    @staticmethod
    def assert_user_not_exist_error(error: Exception):
        assert isinstance(error, ResourceNotFoundError)
        assert_that(error.title, is_('Not Found Error'))
        assert_that(error.parameter, is_('username'))
        assert_that(error.value, is_('ErrorUser'))
        assert_that(error.detail, is_('Could not find user with username: [ErrorUser].'))
        assert_that(error.ref_url, is_('https://api.twitter.com/2/problems/resource-not-found'))

    def test_get_normal_user(self):
        mock_client = Mock()
        mock_client.get_user = MagicMock(return_value=self.normal_user_response)
        client = TweepyHunter(mock_client)

        users, _ = client.observe(username=rx.just("TestUser"))

        users.subscribe(on_next=self.assert_normal_user)
        mock_client.get_user.assert_called_once_with(username='TestUser', **TweepyHunter.user_api_params)

    def test_get_no_pinned_tweet_user(self):
        mock_client = Mock()
        mock_client.get_user = MagicMock(return_value=self.no_pinned_tweet_user_response)
        client = TweepyHunter(mock_client)

        users, _ = client.observe(username=rx.just("NoPinnedTweetUser"))

        users.subscribe(on_next=self.assert_no_pinned_tweet_user)
        mock_client.get_user.assert_called_once_with(username='NoPinnedTweetUser', **TweepyHunter.user_api_params)

    def test_get_not_exist_user(self):
        mock_client = Mock()
        mock_client.get_user = MagicMock(return_value=self.no_pinned_tweet_user_response)
        client = TweepyHunter(mock_client)

        _, errors = client.observe(username=rx.just("ErrorUser"))

        errors.subscribe(on_error=self.assert_user_not_exist_error)
        mock_client.get_user.assert_called_once_with(username='ErrorUser', **TweepyHunter.user_api_params)

    def test_get_users(self):
        def consume(user: User):
            if user.id == 1:
                self.assert_normal_user(user)
            elif user.id == 2:
                self.assert_no_pinned_tweet_user(user)

        client = TweepyHunter.singleton()
        users, errors = client.observe(usernames=rx.just("TwitterDev", "Twitter"))
        users.subscribe(on_next=consume, on_error=self.assert_user_not_exist_error)
