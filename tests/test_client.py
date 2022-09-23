from datetime import datetime
from unittest import mock
from unittest.mock import MagicMock

import pytest
import tweepy
from hamcrest import assert_that, contains_string, is_

from puntgun.client import (
    Client,
    ResourceNotFoundError,
    TwitterApiErrors,
    TwitterClientError,
    paging_api_iter,
    response_to_users,
)
from puntgun.record import Record
from puntgun.rules.data import User


class TestTwitterApiErrors:
    @pytest.fixture
    def errors(self):
        return TwitterApiErrors(
            query_func_name="func",
            query_params={"a": 1},
            resp_errors=[
                {
                    "value": "v",
                    "detail": "d",
                    # the TwitterApiError take this 'title' field as error type.
                    "title": "test api error",
                    "parameter": "p",
                    "type": "t",
                }
            ],
        )

    def test_its_magic_methods(self, errors):
        assert bool(errors) is True
        assert len(errors) == 1
        assert list([e for e in errors])[0] == errors[0]

    def test_transform_between_record(self, errors):
        record: Record = errors.to_record()
        parsed_errors = TwitterApiErrors.parse_from_record(record)

        # check direct fields
        assert record.type == "twitter_api_errors"
        assert record.data.get("query_func_name") == parsed_errors.query_func_name == "func"
        assert record.data.get("query_params") == parsed_errors.query_params == {"a": 1}
        assert len(record.data.get("errors")) == len(parsed_errors) == 1

        # check inner single api error
        error = record.data.get("errors")[0]
        p_error = parsed_errors[0]
        assert error.get("value") == p_error.value == "v"
        assert error.get("detail") == p_error.detail == "d"
        assert error.get("title") == p_error.title == "test api error"
        assert error.get("parameter") == p_error.parameter == "p"
        assert error.get("ref_url") == p_error.ref_url == "t"


create_time = datetime.utcnow()
image_url = "https://example.com"


def response_with(data=None, includes=None, errors=None, meta=None):
    return tweepy.Response(
        data=data if data else [],
        errors=errors if errors else [],
        includes=includes if includes else {},
        meta=meta if meta else {},
    )


@pytest.fixture
def mock_tweepy_client():
    mock_tweepy_client = MagicMock()
    mock_tweepy_client.get_me = MagicMock(return_value=response_with())
    return mock_tweepy_client


@pytest.fixture
def mock_user_getting_tweepy_client(mock_tweepy_client):
    def set_response(test_response_data):
        mock_tweepy_client.get_users = MagicMock(return_value=test_response_data)
        # the logic will get function's __name__ attribute when recording api errors
        mock_tweepy_client.get_users.__name__ = "mock_get_users_func"
        return mock_tweepy_client

    return set_response


@pytest.fixture
def normal_user_response():
    return response_with(
        data=[
            {
                "id": 1,
                "name": "Test User",
                "username": "TestUser",
                "pinned_tweet_id": 1,
                "profile_image_url": image_url,
                "created_at": create_time,
                "description": "hi",
                "location": None,
                "public_metrics": {"followers_count": 1, "following_count": 2, "tweet_count": 3, "listed_count": 4},
                "protected": False,
                "verified": True,
            }
        ],
        includes={"tweets": [{"id": 1, "text": "pinned tweet"}]},
    )


@pytest.fixture
def no_pinned_tweet_user_response():
    return response_with(
        data=[
            {
                "id": 2,
                "name": "No Pinned Tweet User",
                "username": "NoPinnedTweetUser",
                "pinned_tweet_id": None,
                "profile_image_url": image_url,
                "created_at": create_time,
                "description": "hi",
                "location": None,
                "public_metrics": {"followers_count": 1, "following_count": 2, "tweet_count": 3, "listed_count": 4},
                "protected": False,
                "verified": False,
            }
        ]
    )


@pytest.fixture
def not_exist_user_response():
    return response_with(
        errors=[
            {
                "value": "ErrorUser",
                "detail": "Could not find rules with username: [ErrorUser].",
                "title": "Not Found Error",
                "resource_type": "rules",
                "parameter": "username",
                "resource_id": "ErrorUser",
                "type": "https://api.twitter.com/2/problems/resource-not-found",
            }
        ]
    )


@pytest.fixture
def mixed_response(normal_user_response, no_pinned_tweet_user_response, not_exist_user_response):
    """Combine three test responses into one"""
    return response_with(
        data=[normal_user_response.data[0], no_pinned_tweet_user_response.data[0]],
        errors=[not_exist_user_response.errors[0]],
        includes=normal_user_response.includes,
    )


def assert_normal_user(user: User):
    assert_that(user.id, is_(1))
    assert_that(user.name, is_("Test User"))
    assert_that(user.username, is_("TestUser"))
    assert_that(user.pinned_tweet_id, is_(1))
    assert_that(user.pinned_tweet_text, is_("pinned tweet"))
    assert_that(user.verified, is_(True))
    assert_common_user_fields(user)


def assert_no_pinned_tweet_user(user: User):
    assert_that(user.id, is_(2))
    assert_that(user.name, is_("No Pinned Tweet User"))
    assert_that(user.username, is_("NoPinnedTweetUser"))
    # default set to 0
    assert_that(user.pinned_tweet_id, is_(0))
    assert_that(user.pinned_tweet_text, is_(""))
    assert_that(user.verified, is_(False))
    assert_common_user_fields(user)


def assert_common_user_fields(user: User):
    assert_that(user.profile_image_url, is_(image_url))
    assert_that(user.created_at, is_(create_time))
    assert_that(user.description, is_("hi"))
    # default set to ''
    assert_that(user.location, is_(""))
    assert_that(user.followers_count, is_(1))
    assert_that(user.following_count, is_(2))
    assert_that(user.tweet_count, is_(3))
    assert_that(user.protected, is_(False))


def assert_user_not_exist_error(mock_recorder):
    error = mock_recorder.call_args_list[0][0][0][0]
    assert isinstance(error, ResourceNotFoundError)
    assert_that(error.title, is_("Not Found Error"))
    assert_that(error.parameter, is_("username"))
    assert_that(error.value, is_("ErrorUser"))
    assert_that(error.detail, is_("Could not find rules with username: [ErrorUser]."))
    assert_that(error.ref_url, is_("https://api.twitter.com/2/problems/resource-not-found"))


class TestUserQuerying:
    """
    For now, I figure out there are three kinds of rules data in response (responded by Twitter(tweepy.Client)):
        1. rules who has pinned tweet, rules data in "data" field, pinned tweet in "includes.tweets" field
        2. rules who don't have pinned tweet, only rules data in "data" field
        3. rules do not exist (returned in "errors" field)

    The test cases are simulating these situations, test data are from real responses.
    There are some cases also test the constructing and default value replacing logic of :class:`User`.

    We'll test both `get_by_username` and `get_by_id` methods, they are too similar.

    get by id: https://developer.twitter.com/en/docs/twitter-api/users/lookup/api-reference/get-users

    get by username: https://developer.twitter.com/en/docs/twitter-api/users/lookup/api-reference/get-users-by
    """

    def test_response_translating(self, normal_user_response):
        assert_normal_user(response_to_users(normal_user_response)[0])

    def test_tweepy_exception_handling(self, mock_tweepy_client):
        mock_tweepy_client.get_users = MagicMock(side_effect=tweepy.errors.TweepyException("inner"))
        with pytest.raises(TwitterClientError) as e:
            Client(mock_tweepy_client).get_users_by_usernames(["whatever"])
        assert_that(str(e), contains_string("client"))
        assert_that(str(e.value.__cause__), contains_string("inner"))

    def test_get_normal_user(self, normal_user_response, mock_user_getting_tweepy_client):
        assert_normal_user(
            Client(mock_user_getting_tweepy_client(normal_user_response)).get_users_by_usernames(["whatever"])[0]
        )

        assert_normal_user(Client(mock_user_getting_tweepy_client(normal_user_response)).get_users_by_ids([1])[0])

    def test_get_no_pinned_tweet_user(self, no_pinned_tweet_user_response, mock_user_getting_tweepy_client):
        assert_no_pinned_tweet_user(
            Client(mock_user_getting_tweepy_client(no_pinned_tweet_user_response)).get_users_by_usernames(["whatever"])[
                0
            ]
        )

        assert_no_pinned_tweet_user(
            Client(mock_user_getting_tweepy_client(no_pinned_tweet_user_response)).get_users_by_ids([1])[0]
        )

    def test_get_not_exist_user(self, not_exist_user_response, mock_user_getting_tweepy_client, monkeypatch):
        # check get by username method
        mock_recorder = MagicMock()
        monkeypatch.setattr("puntgun.record.Recorder.record", mock_recorder)
        Client(mock_user_getting_tweepy_client(not_exist_user_response)).get_users_by_usernames(["whatever"])
        # recorder received api error
        assert_user_not_exist_error(mock_recorder)

        # check get by id method
        mock_recorder.reset_mock()
        Client(mock_user_getting_tweepy_client(not_exist_user_response)).get_users_by_ids([1])
        assert_user_not_exist_error(mock_recorder)

    def test_get_all_users(self, mixed_response, mock_user_getting_tweepy_client, monkeypatch):
        # check get by username method
        mock_recorder = MagicMock()
        monkeypatch.setattr("puntgun.record.Recorder.record", mock_recorder)
        users = Client(mock_user_getting_tweepy_client(mixed_response)).get_users_by_usernames(["whatever"])
        assert_normal_user(users[0])
        assert_no_pinned_tweet_user(users[1])
        assert_user_not_exist_error(mock_recorder)

        # check get by id method
        mock_recorder.reset_mock()
        users = Client(mock_user_getting_tweepy_client(mixed_response)).get_users_by_ids([1])
        assert_normal_user(users[0])
        assert_no_pinned_tweet_user(users[1])
        assert_user_not_exist_error(mock_recorder)

    def test_pass_more_than_100_users_will_raise_error(self, normal_user_response, mock_user_getting_tweepy_client):
        with pytest.raises(ValueError) as e:
            Client(mock_user_getting_tweepy_client(normal_user_response)).get_users_by_ids(["1"] * 101)
        assert_that(str(e), contains_string("100"))

        with pytest.raises(ValueError) as e:
            Client(mock_user_getting_tweepy_client(normal_user_response)).get_users_by_ids([1] * 101)
        assert_that(str(e), contains_string("100"))


class TestPagedApiQuerier:
    def test_paged_api_querier(self):
        mock_clt_func = MagicMock(
            side_effect=[
                response_with(meta={"next_token": 0}, data=[{"k": 0}]),
                response_with(meta={"next_token": 1}, data=[{"k": 1}]),
                # the last one does not have next_token
                response_with(data=[{"k": 2}]),
            ]
        )
        actual = list(paging_api_iter(mock_clt_func, {"a": "b"}))

        assert mock_clt_func.call_count == 3
        # test return values
        for i in range(3):
            assert actual[i].data[0]["k"] == i
        # test invoking args
        for i in range(1, 3):
            assert mock_clt_func.call_args_list[i] == mock.call(max_results=1000, a="b", pagination_token=i - 1)

    def test_paged_api_querier_with_one_page(self):
        mock_clt_func = MagicMock(return_value=response_with(data=[{"k": 0}]))
        actual = list(paging_api_iter(mock_clt_func, {}))
        assert actual[0].data[0]["k"] == 0


class TestUserPagedApi:
    def test_get_blocked(self, mock_tweepy_client):
        mock_tweepy_client.get_blocked = MagicMock(
            side_effect=[response_with(meta={"next_token": 0}, data=[{"id": 0}]), response_with(data=[{"id": 1}])]
        )
        mock_tweepy_client.get_blocked.__name__ = "mock_get_blocked_func"

        id_list = Client(mock_tweepy_client).cached_blocked_id_list()

        for i in range(2):
            # check user id
            assert id_list[i] == i

    def test_get_following(self, mock_tweepy_client):
        mock_tweepy_client.get_users_following = MagicMock(
            side_effect=[response_with(meta={"next_token": 0}, data=[{"id": 0}]), response_with(data=[{"id": 1}])]
        )
        mock_tweepy_client.get_users_following.__name__ = "mock_get_users_following_func"
        id_list = Client(mock_tweepy_client).cached_following_id_list()
        for i in range(2):
            assert id_list[i] == i

    def test_get_follower(self, mock_tweepy_client):
        mock_tweepy_client.get_users_followers = MagicMock(
            side_effect=[response_with(meta={"next_token": 0}, data=[{"id": 0}]), response_with(data=[{"id": 1}])]
        )
        mock_tweepy_client.get_users_followers.__name__ = "mock_get_users_followers_func"
        id_list = Client(mock_tweepy_client).cached_follower_id_list()
        for i in range(2):
            assert id_list[i] == i


class TestUserBlocking:
    def test_api_response_success(self, mock_tweepy_client):
        mock_tweepy_client.block = MagicMock(return_value=response_with({"blocking": True}))
        assert Client(mock_tweepy_client).block_user_by_id(123)

    def test_api_response_fail(self, mock_tweepy_client):
        mock_tweepy_client.block = MagicMock(return_value=response_with({"blocking": False}))
        assert not Client(mock_tweepy_client).block_user_by_id(123)

    def test_already_blocked(self, mock_tweepy_client):
        # mock already blocked user 0
        mock_tweepy_client.get_blocked = MagicMock(return_value=response_with(data=[{"id": 0}]))
        mock_tweepy_client.get_blocked.__name__ = "mock_get_blocked_func"

        assert Client(mock_tweepy_client).block_user_by_id(0)

    def test_not_block_following(self, mock_tweepy_client, mock_configuration):
        # mock user 0 is follower
        mock_tweepy_client.get_users_following = MagicMock(return_value=response_with(data=[{"id": 0}]))
        mock_tweepy_client.get_users_following.__name__ = "mock_get_users_following_func"
        # set config
        mock_configuration({"block_following": False})

        assert not Client(mock_tweepy_client).block_user_by_id(0)

    def test_not_block_follower(self, mock_tweepy_client, mock_configuration):
        # mock user 0 is follower
        mock_tweepy_client.get_users_followers = MagicMock(return_value=response_with(data=[{"id": 0}]))
        mock_tweepy_client.get_users_followers.__name__ = "mock_get_users_followers_func"
        # set config
        mock_configuration({"block_follower": False})

        assert not Client(mock_tweepy_client).block_user_by_id(0)
