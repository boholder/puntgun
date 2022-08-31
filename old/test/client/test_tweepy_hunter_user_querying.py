from datetime import datetime
from typing import Union
from unittest import TestCase
from unittest.mock import MagicMock, Mock

import reactivex as rx
import tweepy
from hamcrest import assert_that, is_

from old.test import ResourceNotFoundError, TweepyHunter, User


class TestTweepyHunterUserQuerying(TestCase):
    """
    Test the TweepyHunter class's rules information querying method while mocking the tweepy API.
    """

    def test_get_normal_user(self):
        single_user_test("TestUser", normal_user_response, user_assert_func=assert_normal_user)

    def test_get_no_pinned_tweet_user(self):
        single_user_test(
            "NoPinnedTweetUser", no_pinned_tweet_user_response, user_assert_func=assert_no_pinned_tweet_user
        )

    def test_get_not_exist_user(self):
        single_user_test("ErrorUser", not_exist_user_response, error_assert_func=assert_user_not_exist_error)

    def test_split_more_than_100_users_input(self):
        # whatever response mocked
        run_stream(["TestUser"] * 100 + ["LastUser"], normal_user_response, user_assert_func=assert_users)
        # input username list is spilt into two parts, first part has 100 users, second part has the last 1 rules
        mock_tweepy_client.get_users.assert_called_with(usernames=["LastUser"], **TweepyHunter.user_api_params)

    def test_get_users(self):
        run_stream(
            ["NoPinnedTweetUser", "TestUser", "ErrorUser"],
            mixed_response,
            user_assert_func=assert_users,
            error_assert_func=assert_user_not_exist_error,
        )
        mock_tweepy_client.get_users.assert_called_once_with(
            usernames=["NoPinnedTweetUser", "TestUser", "ErrorUser"], **TweepyHunter.user_api_params
        )


def single_user_test(test_user_name: Union[list, str], mock_response, user_assert_func=None, error_assert_func=None):
    run_stream(test_user_name, mock_response, user_assert_func=user_assert_func, error_assert_func=error_assert_func)
    mock_tweepy_client.get_user.assert_called_once_with(username=test_user_name, **TweepyHunter.user_api_params)


def run_stream(test_user_name: Union[list, str], mock_response, user_assert_func=None, error_assert_func=None):
    """Reusable function to do the mock job, run the stream and assert the result"""

    if isinstance(test_user_name, list):
        mock_tweepy_client.get_users = MagicMock(return_value=mock_response)
        result = TweepyHunter(mock_tweepy_client).observe(usernames=test_user_name)
    else:
        mock_tweepy_client.get_user = MagicMock(return_value=mock_response)
        result = TweepyHunter(mock_tweepy_client).observe(username=test_user_name)

    result.subscribe_on_model(rx.Observer(on_next=user_assert_func)).subscribe_on_error(
        rx.Observer(on_next=error_assert_func)
    ).wire()


# These test data based on real responses of Twitter API
create_time = datetime.now()
image_url = "https://example.com"

normal_user_response = tweepy.Response(
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
    meta={},
    errors=[],
)

no_pinned_tweet_user_response = tweepy.Response(
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
    ],
    errors=[],
    includes={},
    meta={},
)

not_exist_user_response = tweepy.Response(
    data=None,
    includes={},
    meta={},
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
    ],
)

mixed_response = tweepy.Response(
    data=[normal_user_response.data[0], no_pinned_tweet_user_response.data[0]],
    errors=[not_exist_user_response.errors[0]],
    includes=normal_user_response.includes,
    meta={},
)

mock_tweepy_client = Mock()

# the tweepy hunter will query auth rules's info when initialing, mock it,
# though we don't need to test this part
mock_tweepy_client.get_me = MagicMock(return_value=normal_user_response)


def assert_normal_user(user: User):
    assert_that(user.id, is_(1))
    assert_that(user.name, is_("Test User"))
    assert_that(user.username, is_("TestUser"))
    assert_that(user.pinned_tweet_id, is_(1))
    assert_that(user.profile_image_url, is_(image_url))
    assert_that(user.created_at, is_(create_time))
    assert_that(user.description, is_("hi"))
    assert_that(user.location, is_(None))
    assert_that(user.followers_count, is_(1))
    assert_that(user.following_count, is_(2))
    assert_that(user.tweet_count, is_(3))
    assert_that(user.protected, is_(False))
    assert_that(user.verified, is_(True))
    assert_that(user.pinned_tweet_text, is_("pinned tweet"))
    print("assert normal rules success")


def assert_no_pinned_tweet_user(user: User):
    assert_that(user.id, is_(2))
    assert_that(user.name, is_("No Pinned Tweet User"))
    assert_that(user.username, is_("NoPinnedTweetUser"))
    assert_that(user.pinned_tweet_id, is_(None))
    assert_that(user.profile_image_url, is_(image_url))
    assert_that(user.created_at, is_(create_time))
    assert_that(user.description, is_("hi"))
    assert_that(user.location, is_(None))
    assert_that(user.followers_count, is_(1))
    assert_that(user.following_count, is_(2))
    assert_that(user.tweet_count, is_(3))
    assert_that(user.protected, is_(False))
    assert_that(user.verified, is_(False))
    assert_that(user.pinned_tweet_text, is_(""))
    print("assert no pinned tweet rules success")


def assert_user_not_exist_error(error: Exception):
    assert isinstance(error, ResourceNotFoundError)
    assert_that(error.title, is_("Not Found Error"))
    assert_that(error.parameter, is_("username"))
    assert_that(error.value, is_("ErrorUser"))
    assert_that(error.detail, is_("Could not find rules with username: [ErrorUser]."))
    assert_that(error.ref_url, is_("https://api.twitter.com/2/problems/resource-not-found"))
    print("assert rules not exist error success")


def assert_users(user: User):
    if user.id == 1:
        assert_normal_user(user)
    elif user.id == 2:
        assert_no_pinned_tweet_user(user)
