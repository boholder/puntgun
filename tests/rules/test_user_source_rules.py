from unittest.mock import MagicMock, call

import pytest
import reactivex as rx
import reactivex.operators as op
from hamcrest import all_of, assert_that, contains_string
from reactivex.internal import SequenceContainsNoElementsError

from puntgun import client
from puntgun.rules.config_parser import ConfigParser
from puntgun.rules.data import User
from puntgun.rules.user.source_rules import (
    MyFollowerUserSourceRule,
    NameUserSourceRule,
    UserSourceRule,
)


class TestCommonBehavior:
    def test_client_error_catching(self, mock_client):
        def raise_error(_):
            raise_error.called = True
            raise client.TwitterClientError()

        def assertion_consumer(e):
            assertion_consumer.called = True
            assert_that(str(e), contains_string("client"))

        mock_client.get_users_by_usernames = raise_error
        rule = NameUserSourceRule.parse_obj({"names": ["uname"]})

        # the error will be raised out of the pipeline
        with pytest.raises(client.TwitterClientError) as e:
            rule().pipe(op.do(rx.Observer(on_error=assertion_consumer))).run()

        assert_that(str(e), contains_string("client"))
        assert raise_error.called
        assert assertion_consumer.called

    def test_what_happen_when_client_returns_empty_list_as_result(self, mock_client):
        # the client returns an empty list
        mock_get_users_by_usernames = MagicMock(return_value=[])
        mock_client.get_users_by_usernames = mock_get_users_by_usernames
        rule = NameUserSourceRule.parse_obj({"names": ["uname"]})

        # will raise an error inside reactivex
        with pytest.raises(SequenceContainsNoElementsError) as e:
            rule().pipe(op.do(rx.Observer(on_next=lambda _: None))).run()
        assert str(e.value) == "Sequence contains no elements"

    def test_when_not_all_calls_to_client_return_empty_list(self, mock_client, user_id_sequence_checker):
        # as long as not all calls to the client returns empty lists, it's ok
        mock_get_users_by_usernames = MagicMock(side_effect=[[User(id=i) for i in range(100)], [User(id=100)]])
        mock_client.get_users_by_usernames = mock_get_users_by_usernames
        rule = NameUserSourceRule.parse_obj({"names": ["first_request"] * 100 + ["second_request"]})

        rule().pipe(op.do(rx.Observer(on_next=user_id_sequence_checker))).run()
        # called client function twice
        assert mock_get_users_by_usernames.call_count == 2
        assert mock_get_users_by_usernames.call_args_list[0] == call(["first_request"] * 100)
        assert mock_get_users_by_usernames.call_args_list[1] == call(["second_request"])
        # called subscriber function with User(id=0)...User(id=100)
        assert user_id_sequence_checker.call_count == 101

    def test_execute_with_less_than_100_names(self, mock_client, user_id_sequence_checker):
        # as long as not all calls to the client returns empty lists, it's ok
        mock_get_users_by_usernames = MagicMock(side_effect=[[User(id=0), User(id=1)]])
        mock_client.get_users_by_usernames = mock_get_users_by_usernames
        rule = NameUserSourceRule.parse_obj({"names": ["first_request", "second_request"]})

        rule().pipe(op.do(rx.Observer(on_next=user_id_sequence_checker))).run()
        assert mock_get_users_by_usernames.call_count == 1
        assert user_id_sequence_checker.call_count == 2
        assert mock_get_users_by_usernames.call_args_list[0] == call(["first_request", "second_request"])


def test_name_user_source_rule(mock_client, user_id_sequence_checker):
    mock_get_users_by_usernames = MagicMock(side_effect=[[User(id=0)], [User(id=1)]])
    mock_client.get_users_by_usernames = mock_get_users_by_usernames
    rule = ConfigParser.parse({"names": ["first_request"] * 100 + ["second_request"]}, UserSourceRule)
    # use the Observable.run() to synchronously start and finish the pipeline.
    rule().pipe(op.do(rx.Observer(on_next=user_id_sequence_checker))).run()

    # the rule splits the parameter's value into two list
    # and makes two calls to the client
    assert mock_get_users_by_usernames.call_count == user_id_sequence_checker.call_count == 2
    assert mock_get_users_by_usernames.call_args_list[0] == call(["first_request"] * 100)
    assert mock_get_users_by_usernames.call_args_list[1] == call(["second_request"])


def test_id_user_source_rule(mock_client, user_id_sequence_checker):
    mock_get_users_by_ids = MagicMock(side_effect=[[User(id=0)], [User(id=1)]])
    mock_client.get_users_by_ids = mock_get_users_by_ids
    rule = ConfigParser.parse({"ids": [1] * 100 + [2]}, UserSourceRule)
    # use the Observable.run() to synchronously start and finish the pipeline.
    rule().pipe(op.do(rx.Observer(on_next=user_id_sequence_checker))).run()

    # the rule splits the parameter's value into two list
    # and makes two calls to the client
    assert mock_get_users_by_ids.call_count == user_id_sequence_checker.call_count == 2
    assert mock_get_users_by_ids.call_args_list[0] == call([1] * 100)
    assert mock_get_users_by_ids.call_args_list[1] == call([2])


class TestMyFollowerUserSourceRule:
    @pytest.fixture
    def mock_client_cached_follower_func(self, mock_client):
        mock_users = [User(id=i, username=str(i)) for i in range(4)]
        mock_func = MagicMock(return_value=mock_users)
        mock_client.cached_follower = mock_func
        return mock_func

    def test_fields_conflicting(self):
        with pytest.raises(Exception) as e:
            MyFollowerUserSourceRule.parse_from_config({"my_followers": {"first": 1, "last": 1, "after_user": "n"}})

        assert_that(
            str(e),
            all_of(
                contains_string("conflict"),
                contains_string("first"),
                contains_string("last"),
                contains_string("after_user"),
            ),
        )

    def test_no_field(self, mock_client_cached_follower_func, user_id_sequence_checker):
        rule = ConfigParser.parse({"my_followers": {}}, UserSourceRule)
        rule().pipe(op.do(rx.Observer(on_next=user_id_sequence_checker))).run()
        # 0 to 4
        assert user_id_sequence_checker.call_count == 4
        assert user_id_sequence_checker.called_user_ids == {0, 1, 2, 3}

    def test_last_field(self, mock_client_cached_follower_func, user_id_sequence_checker):
        rule = MyFollowerUserSourceRule(last=2)
        rule().pipe(op.do(rx.Observer(on_next=user_id_sequence_checker))).run()
        assert user_id_sequence_checker.call_count == 2
        assert user_id_sequence_checker.called_user_ids == {0, 1}

    def test_first_field(self, mock_client_cached_follower_func, user_id_sequence_checker):
        rule = MyFollowerUserSourceRule(first=2)
        rule().pipe(op.do(rx.Observer(on_next=user_id_sequence_checker))).run()
        assert user_id_sequence_checker.call_count == 2
        assert user_id_sequence_checker.called_user_ids == {2, 3}

    def test_after_user_field_exists(self, mock_client_cached_follower_func, user_id_sequence_checker):
        rule = MyFollowerUserSourceRule(after_user="3")
        rule().pipe(op.do(rx.Observer(on_next=user_id_sequence_checker))).run()
        assert user_id_sequence_checker.call_count == 3
        assert user_id_sequence_checker.called_user_ids == {0, 1, 2}

    def test_after_user_field_not_exists(self, mock_client_cached_follower_func):
        rule = MyFollowerUserSourceRule(after_user="this-user-not-exist")
        with pytest.raises(rx.internal.exceptions.SequenceContainsNoElementsError):
            rule().pipe(op.do(rx.Observer(on_next=lambda x: print(x)))).run()
