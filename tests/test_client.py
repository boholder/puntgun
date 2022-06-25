from datetime import datetime
from unittest.mock import MagicMock, Mock

import pytest
import tweepy
from hamcrest import assert_that, is_

from client import Client, ResourceNotFoundError
from rules.user import User

create_time = datetime.now()
image_url = 'https://example.com'


class TestUserQuerying:
    """
    For now, I figure out there are three kinds of rules datas in response (responded by Twitter(tweepy.Client)):
        1. rules who has pinned tweet, rules data in "data" field, pinned tweet in "includes.tweets" field
        2. rules who doesn't have pinned tweet, only rules data in "data" field
        3. rules does not exist (returned in "errors" field)

    The test cases are simulating these situations, test datas are from real responses.
    There are some cases also test the constructing and default value replacing logic of :class:`User`.

    get by id: https://developer.twitter.com/en/docs/twitter-api/users/lookup/api-reference/get-users

    get by username: https://developer.twitter.com/en/docs/twitter-api/users/lookup/api-reference/get-users-by
    """

    def test_response_translating(self, normal_user_response):
        self.assert_normal_user(Client._Client__user_resp_to_user_instances(normal_user_response)[0])

    def test_get_normal_user(self, normal_user_response, mock_tweepy_client):
        self.assert_normal_user(
            Client(mock_tweepy_client(normal_user_response)).get_users_by_usernames(['whatever'])[0])
        self.assert_normal_user(
            Client(mock_tweepy_client(normal_user_response)).get_users_by_ids([1])[0])

    def test_get_no_pinned_tweet_user(self, no_pinned_tweet_user_response, mock_tweepy_client):
        self.assert_no_pinned_tweet_user(
            Client(mock_tweepy_client(no_pinned_tweet_user_response)).get_users_by_usernames(['whatever'])[0])
        self.assert_no_pinned_tweet_user(
            Client(mock_tweepy_client(no_pinned_tweet_user_response)).get_users_by_ids([1])[0])

    def test_get_not_exist_user(self, not_exist_user_response, mock_tweepy_client, monkeypatch):
        # check get by username method
        mock_recorder = MagicMock()
        monkeypatch.setattr('recorder.Recorder.record', mock_recorder)
        Client(mock_tweepy_client(not_exist_user_response)).get_users_by_usernames(['whatever'])
        # recorder received api error
        self.assert_user_not_exist_error(mock_recorder)

        # check get by id method
        mock_recorder.reset_mock()
        Client(mock_tweepy_client(not_exist_user_response)).get_users_by_ids([1])
        self.assert_user_not_exist_error(mock_recorder)

    def test_get_all_users(self, mixed_response, mock_tweepy_client, monkeypatch):
        # check get by username method
        mock_recorder = MagicMock()
        monkeypatch.setattr('recorder.Recorder.record', mock_recorder)
        users = Client(mock_tweepy_client(mixed_response)).get_users_by_usernames(['whatever'])
        self.assert_normal_user(users[0])
        self.assert_no_pinned_tweet_user(users[1])
        self.assert_user_not_exist_error(mock_recorder)

        # check get by id method
        mock_recorder.reset_mock()
        users = Client(mock_tweepy_client(mixed_response)).get_users_by_ids([1])
        self.assert_normal_user(users[0])
        self.assert_no_pinned_tweet_user(users[1])
        self.assert_user_not_exist_error(mock_recorder)

    @pytest.fixture
    def mock_tweepy_client(self):
        mock_tweepy_client = Mock()
        mock_tweepy_client.get_me = MagicMock(return_value={'data': None})

        def set_response(test_response_data):
            mock_tweepy_client.get_users = MagicMock(return_value=test_response_data)
            return mock_tweepy_client

        return set_response

    @pytest.fixture
    def normal_user_response(self):
        return tweepy.Response(data=[{'id': 1, 'name': 'Test User', 'username': 'TestUser',
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

    @pytest.fixture
    def no_pinned_tweet_user_response(self):
        return tweepy.Response(data=[{'id': 2, 'name': 'No Pinned Tweet User',
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

    @pytest.fixture
    def not_exist_user_response(self):
        return tweepy.Response(data=None, includes={}, meta={},
                               errors=[{'value': 'ErrorUser',
                                        'detail': 'Could not find rules with username: [ErrorUser].',
                                        'title': 'Not Found Error', 'resource_type': 'rules',
                                        'parameter': 'username',
                                        'resource_id': 'ErrorUser',
                                        'type': 'https://api.twitter.com/2/problems/resource-not-found'}]
                               )

    @pytest.fixture
    def mixed_response(self, normal_user_response, no_pinned_tweet_user_response, not_exist_user_response):
        """Combine three test responses into one"""
        return tweepy.Response(data=[normal_user_response.data[0], no_pinned_tweet_user_response.data[0]],
                               errors=[not_exist_user_response.errors[0]],
                               includes=normal_user_response.includes,
                               meta={})

    @staticmethod
    def assert_normal_user(user: User):
        assert_that(user.id, is_(1))
        assert_that(user.name, is_('Test User'))
        assert_that(user.username, is_('TestUser'))
        assert_that(user.pinned_tweet_id, is_(1))
        assert_that(user.pinned_tweet_text, is_('pinned tweet'))
        assert_that(user.verified, is_(True))
        TestUserQuerying.assert_same_user_info(user)

    @staticmethod
    def assert_no_pinned_tweet_user(user: User):
        assert_that(user.id, is_(2))
        assert_that(user.name, is_('No Pinned Tweet User'))
        assert_that(user.username, is_('NoPinnedTweetUser'))
        # default set to 0
        assert_that(user.pinned_tweet_id, is_(0))
        assert_that(user.pinned_tweet_text, is_(''))
        assert_that(user.verified, is_(False))
        TestUserQuerying.assert_same_user_info(user)

    @staticmethod
    def assert_same_user_info(user: User):
        assert_that(user.profile_image_url, is_(image_url))
        assert_that(user.created_at, is_(create_time))
        assert_that(user.description, is_('hi'))
        # default set to ''
        assert_that(user.location, is_(''))
        assert_that(user.followers_count, is_(1))
        assert_that(user.following_count, is_(2))
        assert_that(user.tweet_count, is_(3))
        assert_that(user.protected, is_(False))

    @staticmethod
    def assert_user_not_exist_error(mock_recorder):
        error = mock_recorder.call_args_list[0][0][0][0]
        assert isinstance(error, ResourceNotFoundError)
        assert_that(error.title, is_('Not Found Error'))
        assert_that(error.parameter, is_('username'))
        assert_that(error.value, is_('ErrorUser'))
        assert_that(error.detail, is_('Could not find rules with username: [ErrorUser].'))
        assert_that(error.ref_url, is_('https://api.twitter.com/2/problems/resource-not-found'))
