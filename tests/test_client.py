import datetime
from unittest import mock
from unittest.mock import MagicMock

import pytest
import tweepy
from hamcrest import assert_that, contains_string

from puntgun.client import (
    Client,
    ResourceNotFoundError,
    TwitterApiErrors,
    TwitterClientError,
    paged_api_iter,
    response_to_tweets,
    response_to_users,
)
from puntgun.record import Record
from puntgun.rules.data import (
    ContextAnnotation,
    Place,
    Poll,
    ReplySettings,
    Tweet,
    User,
)


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


class TestUserQuerying:
    """
    For now, I figure out there are three kinds of users data in response (responded by Twitter(tweepy.Client)):
        1. users who has pinned tweet, user data in "data" field, pinned tweet in "includes.tweets" field
        2. users who don't have pinned tweet, only user data in "data" field
        3. users do not exist (returned in "errors" field)

    The test cases are simulating these situations, test data are from real responses.
    There are some cases also test the constructing and default value replacing logic of :class:`User`.
    We'll cover `get_by_username`, `get_by_id` methods and `User` class in these cases.

    get by id: https://developer.twitter.com/en/docs/twitter-api/users/lookup/api-reference/get-users
    get by username: https://developer.twitter.com/en/docs/twitter-api/users/lookup/api-reference/get-users-by
    """

    def test_response_transformation(self, normal_user_response):
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


class TestPagedApiIter:
    def test_paged_api_querier(self):
        mock_clt_func = MagicMock(
            side_effect=[
                response_with(meta={"next_token": 0}, data=[{"k": 0}]),
                response_with(meta={"next_token": 1}, data=[{"k": 1}]),
                # the last one does not have next_token
                response_with(data=[{"k": 2}]),
            ]
        )
        actual = list(paged_api_iter(mock_clt_func, {"a": "b"}))

        assert mock_clt_func.call_count == 3
        # test return values
        for i in range(3):
            assert actual[i].data[0]["k"] == i
        # test invoking args
        for i in range(1, 3):
            assert mock_clt_func.call_args_list[i] == mock.call(max_results=1000, a="b", pagination_token=i - 1)

    def test_paged_api_querier_with_one_page(self):
        mock_clt_func = MagicMock(return_value=response_with(data=[{"k": 0}]))
        actual = list(paged_api_iter(mock_clt_func, {}))
        assert actual[0].data[0]["k"] == 0


class TestPagedUserApi:
    def test_get_blocked(self, mock_tweepy_client):
        # the client will transform the {"id": 0} into User(id=0)
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

    def test_get_users_who_like_tweet(self, mock_tweepy_client):
        mock_tweepy_client.get_liking_users = MagicMock(
            side_effect=[response_with(meta={"next_token": 0}, data=[{"id": 0}]), response_with(data=[{"id": 1}])]
        )
        mock_tweepy_client.get_liking_users.__name__ = "mock_get_users_who_like_tweet_func"
        users = Client(mock_tweepy_client).get_users_who_like_tweet(123)
        for i in range(2):
            assert users[i].id == i

    def test_get_users_who_retweet_tweet(self, mock_tweepy_client):
        mock_tweepy_client.get_retweeters = MagicMock(
            side_effect=[response_with(meta={"next_token": 0}, data=[{"id": 0}]), response_with(data=[{"id": 1}])]
        )
        mock_tweepy_client.get_retweeters.__name__ = "mock_get_users_who_retweet_tweet_func"
        users = Client(mock_tweepy_client).get_users_who_retweet_tweet(123)
        for i in range(2):
            assert users[i].id == i


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


class TestTweetQuerying:
    """
    The structural complexity and content diversity of Tweet entity is far exceeds that of User entity,
    and I can not find all types of samples to verify the completeness of the code's special case handling.
    I completed the development of Tweet DTO class (and Media, Poll, Place DTO classes which are contained in Tweet)
    and the basic querying API by reading the official documentation
    and observing a small number of samples (in check_tweepy_behaviors.py).

    https://developer.twitter.com/en/docs/twitter-api/tweets/lookup/api-reference/get-tweets
    """

    def test_response_transformation(self, full_tweet_response):
        assert_full_tweet(response_to_tweets(full_tweet_response)[0])

    def test_get_basic_fields_tweet(self, mock_tweet_getting_tweepy_client, basic_tweet_response):
        """Test if Tweet DTO can convert None values into default values."""
        assert_basic_tweet(Client(mock_tweet_getting_tweepy_client(basic_tweet_response)).get_tweets_by_ids([1])[0])

    def test_get_full_fields_tweet(self, mock_tweet_getting_tweepy_client, full_tweet_response):
        """Test if Tweet DTO can handle optional information like location, attachments..."""
        assert_full_tweet(Client(mock_tweet_getting_tweepy_client(full_tweet_response)).get_tweets_by_ids([1])[0])


test_time = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
test_url = "https://example.com"
common_user_data = {
    "profile_image_url": test_url,
    "created_at": test_time.isoformat(),
    "description": "hi",
    "location": None,
    "public_metrics": {"followers_count": 1, "following_count": 2, "tweet_count": 3, "listed_count": 4},
    "protected": False,
}

normal_user_data = {
    "id": 1,
    "name": "Test User",
    "username": "TestUser",
    "pinned_tweet_id": 1,
    "verified": True,
    "url": test_url,
    "entities": {"url": {"urls": [{"url": test_url, "expanded_url": "exp"}]}},
}
normal_user_data.update(common_user_data)

no_pinned_tweet_user_data = {
    "id": 2,
    "name": "No Pinned Tweet User",
    "username": "NoPinnedTweetUser",
    "pinned_tweet_id": None,
    "verified": False,
}
no_pinned_tweet_user_data.update(common_user_data)


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
        data=[tweepy.User(normal_user_data)],
        includes={"tweets": [{"id": 1, "text": "pinned tweet"}]},
    )


@pytest.fixture
def no_pinned_tweet_user_response():
    return response_with(data=[tweepy.User(no_pinned_tweet_user_data)])


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
    assert user.id == 1
    assert user.name == "Test User"
    assert user.username == "TestUser"
    assert user.pinned_tweet_id == 1
    assert user.pinned_tweet_text == "pinned tweet"
    assert user.verified is True
    assert_common_user_fields(user)
    assert user.url == "exp"


def assert_no_pinned_tweet_user(user: User):
    assert user.id == 2
    assert user.name == "No Pinned Tweet User"
    assert user.username == "NoPinnedTweetUser"
    # default set to 0
    assert user.pinned_tweet_id == 0
    assert user.pinned_tweet_text == ""
    assert user.verified is False
    assert_common_user_fields(user)


def assert_common_user_fields(user: User):
    assert user.profile_image_url == test_url
    assert user.created_at == test_time
    assert user.description == "hi"
    assert user.location == ""
    assert user.followers_count == 1
    assert user.following_count == 2
    assert user.tweet_count == 3
    assert user.protected is False


def assert_user_not_exist_error(mock_recorder):
    error = mock_recorder.call_args_list[0][0][0][0]
    assert isinstance(error, ResourceNotFoundError)
    assert error.title == "Not Found Error"
    assert error.parameter == "username"
    assert error.value == "ErrorUser"
    assert error.detail == "Could not find rules with username: [ErrorUser]."
    assert error.ref_url == "https://api.twitter.com/2/problems/resource-not-found"


@pytest.fixture
def mock_tweet_getting_tweepy_client(mock_tweepy_client):
    def set_response(test_response_data):
        mock_tweepy_client.get_tweets = MagicMock(return_value=test_response_data)
        # the logic will get function's __name__ attribute when recording api errors
        mock_tweepy_client.get_tweets.__name__ = "mock_get_tweets_func"
        return mock_tweepy_client

    return set_response


common_tweet_data = {
    "author_id": 1,
    "created_at": test_time,
    "possibly_sensitive": False,
    "text": "text",
    "public_metrics": {"retweet_count": 1, "reply_count": 1, "like_count": 1, "quote_count": 1},
    "reply_settings": "following",
    "conversation_id": 123,
}
basic_tweet_data = {
    "id": 1,
    "context_annotations": None,
    "withheld": None,
    "in_reply_to_user_id": None,
    "referenced_tweets": None,
    "source": None,
    "attachments": None,
    "geo": None,
    "lang": None,
    "entities": None,
}
basic_tweet_data.update(common_tweet_data)


@pytest.fixture
def basic_tweet_response():
    return response_with(data=[basic_tweet_data], includes={"users": [normal_user_data]})


@pytest.fixture
def full_tweet_response():
    data = {
        "id": 2,
        "context_annotations": [
            {
                "domain": {"id": "1", "name": "dn", "description": "dhi"},
                "entity": {"id": "2", "name": "en", "description": "ehi"},
            }
        ],
        "withheld": {"a": 123},
        "in_reply_to_user_id": 2,
        "referenced_tweets": [{"id": 1, "type": "quoted"}],
        "source": "App",
        "attachments": {"media_keys": ["1", "2"], "poll_ids": ["1"]},
        "geo": {"place_id": "1"},
        "lang": "en",
        "entities": {"a": 123},
    }
    data.update(common_tweet_data)
    return response_with(
        data=[data],
        includes={
            "users": [normal_user_data],
            "media": [
                {
                    "media_key": "1",
                    "type": "photo",
                    "alt_text": "alt",
                    "height": 123,
                    "width": 456,
                    "duration_ms": None,
                    "url": test_url,
                },
                {
                    "media_key": "2",
                    "type": "video",
                    "alt_text": None,
                    "height": 123,
                    "width": 456,
                    "duration_ms": 789,
                    "preview_image_url": test_url,
                    "public_metrics": {"view_count": 2901},
                    "url": None,
                },
            ],
            "tweets": [basic_tweet_data],
            "polls": [
                {
                    "id": "1",
                    "duration_minutes": 123,
                    "end_datetime": test_time,
                    "voting_status": "open",
                    "options": [{"position": 1, "label": "A", "votes": 1}, {"position": 2, "label": "B", "votes": 2}],
                }
            ],
            "places": [
                {
                    "geo": {"a": 123},
                    "country_code": "US",
                    "name": "Manhattan",
                    "id": "1",
                    "place_type": "city",
                    "country": "United States",
                    "full_name": "Manhattan, NY",
                }
            ],
        },
    )


def assert_basic_tweet(tweet: Tweet):
    assert tweet.id == 1
    assert tweet.context_annotations == []
    assert tweet.withheld == {}
    assert tweet.in_reply_to_user_id == 0
    assert tweet.referenced_tweets == []
    assert tweet.related_tweets == {}
    assert tweet.source == ""
    assert tweet.attachments == {}
    assert tweet.mediums == []
    assert tweet.polls == []
    assert tweet.geo == {}
    assert tweet.place == Place()
    assert tweet.lang == ""
    assert tweet.entities == {}
    assert_common_tweet_fields(tweet)


def assert_full_tweet(tweet: Tweet):
    assert tweet.id == 2
    assert tweet.context_annotations == [
        ContextAnnotation(
            domain=ContextAnnotation.Domain(id="1", name="dn", description="dhi"),
            entity=ContextAnnotation.Entity(id="2", name="en", description="ehi"),
        )
    ]
    assert tweet.withheld == {"a": 123}
    assert tweet.in_reply_to_user_id == 2
    assert tweet.referenced_tweets == [{"id": 1, "type": "quoted"}]
    assert tweet.related_tweets["quoted"][0].id == 1
    assert tweet.source == "App"
    assert tweet.attachments == {"media_keys": ["1", "2"], "poll_ids": ["1"]}

    photo = tweet.mediums[0]
    assert photo.media_key == "1"
    assert photo.type == "photo"
    assert photo.alt_text == "alt"
    assert photo.height == 123
    assert photo.width == 456
    assert photo.duration_ms is None
    assert photo.url == test_url

    video = tweet.mediums[1]
    assert video.media_key == "2"
    assert video.type == "video"
    assert video.alt_text is None
    assert video.height == 123
    assert video.width == 456
    assert video.duration_ms == 789
    assert video.url is None
    assert video.preview_image_url == test_url
    assert video.public_metrics == {"view_count": 2901}

    poll = tweet.polls[0]
    assert poll.id == "1"
    assert poll.duration_minutes == 123
    assert poll.end_datetime == test_time
    assert poll.voting_status == Poll.Status.OPEN
    assert poll.options == [Poll.Option(position=1, label="A", votes=1), Poll.Option(position=2, label="B", votes=2)]

    assert tweet.geo == {"place_id": "1"}
    assert tweet.place.id == "1"
    assert tweet.place.name == "Manhattan"
    assert tweet.place.full_name == "Manhattan, NY"
    assert tweet.place.place_type == "city"
    assert tweet.place.contained_with == []
    assert tweet.place.country == "United States"
    assert tweet.place.country_code == "US"
    assert tweet.place.geo == {"a": 123}

    assert tweet.lang == "en"
    assert tweet.entities == {"a": 123}
    assert_common_tweet_fields(tweet)


def assert_common_tweet_fields(tweet: Tweet):
    assert tweet.author.name == "Test User"
    assert tweet.created_at == test_time
    assert tweet.possibly_sensitive is False
    assert tweet.text == "text"
    assert tweet.retweet_count == 1
    assert tweet.reply_count == 1
    assert tweet.like_count == 1
    assert tweet.quote_count == 1
    assert tweet.reply_settings == ReplySettings.FOLLOWING
    assert tweet.conversation_id == 123
