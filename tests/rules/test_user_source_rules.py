from unittest.mock import MagicMock, call

import pytest
import reactivex as rx
import reactivex.operators as ops
from reactivex.internal import SequenceContainsNoElementsError

import client
from rules.config_parser import ConfigParser
from rules.user import User
from rules.user.source_rules import NameUserSourceRule, UserSourceRule


class TestCommonBehavior:

    def test_client_error_catching(self, mock_client):
        def raise_error(_):
            raise_error.called = True
            raise client.TwitterClientError('error')

        def assertion_consumer(e):
            assertion_consumer.called = True
            assert str(e) == 'error'

        mock_client.get_users_by_usernames = raise_error
        rule = NameUserSourceRule.parse_obj({'names': ['uname']})

        # the error will be raised out of the pipeline
        with pytest.raises(client.TwitterClientError) as actual_error:
            rule().pipe(ops.do(rx.Observer(on_error=assertion_consumer))).run()

        assert str(actual_error.value) == 'error'
        assert raise_error.called
        assert assertion_consumer.called

    def test_what_happen_when_client_returns_empty_list_as_result(self, mock_client):
        # the client returns an empty list
        mock_get_users_by_usernames = MagicMock(return_value=[])
        mock_client.get_users_by_usernames = mock_get_users_by_usernames
        rule = NameUserSourceRule.parse_obj({'names': ['uname']})

        # will raise an error inside reactivex
        with pytest.raises(SequenceContainsNoElementsError) as actual_error:
            rule().pipe(ops.do(rx.Observer(on_next=lambda _: None))).run()
        assert str(actual_error.value) == 'Sequence contains no elements'

    def test_when_not_all_calls_to_client_return_empty_list(self, mock_client, user_id_sequence_checker):
        # as long as not all calls to the client returns empty lists, it's ok
        mock_get_users_by_usernames = MagicMock(side_effect=[[], [User(id=0)]])
        mock_client.get_users_by_usernames = mock_get_users_by_usernames
        rule = NameUserSourceRule.parse_obj({'names': ['first_request'] * 100 + ['second_request']})

        rule().pipe(ops.do(rx.Observer(on_next=user_id_sequence_checker))).run()
        assert mock_get_users_by_usernames.call_count == 2
        assert user_id_sequence_checker.call_count == 1
        assert mock_get_users_by_usernames.call_args_list[1] == call(['second_request'])


def test_name_user_source_rule(mock_client, user_id_sequence_checker):
    mock_get_users_by_usernames = MagicMock(side_effect=[[User(id=0)], [User(id=1)]])
    mock_client.get_users_by_usernames = mock_get_users_by_usernames
    rule = ConfigParser.parse({'names': ['first_request'] * 100 + ['second_request']}, UserSourceRule)
    # use the Observable.run() to synchronously start and finish the pipeline.
    rule().pipe(ops.do(rx.Observer(on_next=user_id_sequence_checker))).run()

    # the rule splits the parameter's value into two list
    # and makes two calls to the client
    assert mock_get_users_by_usernames.call_count == user_id_sequence_checker.call_count == 2
    assert mock_get_users_by_usernames.call_args_list[0] == call(['first_request'] * 100)
    assert mock_get_users_by_usernames.call_args_list[1] == call(['second_request'])


def test_id_user_source_rule(mock_client, user_id_sequence_checker):
    mock_get_users_by_ids = MagicMock(side_effect=[[User(id=0)], [User(id=1)]])
    mock_client.get_users_by_ids = mock_get_users_by_ids
    rule = ConfigParser.parse({'ids': [1] * 100 + [2]}, UserSourceRule)
    # use the Observable.run() to synchronously start and finish the pipeline.
    rule().pipe(ops.do(rx.Observer(on_next=user_id_sequence_checker))).run()

    # the rule splits the parameter's value into two list
    # and makes two calls to the client
    assert mock_get_users_by_ids.call_count == user_id_sequence_checker.call_count == 2
    assert mock_get_users_by_ids.call_args_list[0] == call([1] * 100)
    assert mock_get_users_by_ids.call_args_list[1] == call([2])
