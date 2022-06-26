from unittest.mock import MagicMock, call

import pytest
import reactivex as rx
import reactivex.operators as ops
from reactivex.internal import SequenceContainsNoElementsError

import client
from rules.user import User
from rules.user.source_rules import NameUserSourceRule, IdUserSourceRule


def test_name_user_source_rule(mock_client):
    count = 0

    def assertion(u):
        nonlocal count
        count += 1
        assert u.id == 1

    mock_get_users_by_usernames = MagicMock(side_effect=[[User(id=1)], [User(id=1)]])
    mock_client.get_users_by_usernames = mock_get_users_by_usernames
    rule = NameUserSourceRule.parse_obj({'names': ['first_request'] * 100 + ['second_request']})
    # use the Observable.run() to synchronously start and finish the pipeline.
    rule().pipe(ops.do(rx.Observer(on_next=assertion))).run()

    # the rule splits the parameter's value into two list
    # and makes two calls to the client
    assert mock_get_users_by_usernames.call_count == count == 2
    assert mock_get_users_by_usernames.call_args_list[0] == call(['first_request'] * 100)
    assert mock_get_users_by_usernames.call_args_list[1] == call(['second_request'])


def test_client_error_catching(mock_client):
    def raise_error(_):
        raise client.TwitterClientError('error')

    def assertion_consumer(e):
        assert str(e) == 'error'

    mock_client.get_users_by_usernames = raise_error
    rule = NameUserSourceRule.parse_obj({'names': ['uname']})

    # the error will be raised out of the pipeline
    with pytest.raises(client.TwitterClientError) as actual_error:
        rule().pipe(ops.do(rx.Observer(on_error=assertion_consumer))).run()

    assert str(actual_error.value) == 'error'


def test_what_happen_when_client_returns_empty_list_as_result(mock_client):
    # the client returns an empty list
    mock_get_users_by_usernames = MagicMock(return_value=[])
    mock_client.get_users_by_usernames = mock_get_users_by_usernames
    rule = NameUserSourceRule.parse_obj({'names': ['uname']})

    # will raise an error inside reactivex
    with pytest.raises(SequenceContainsNoElementsError) as actual_error:
        rule().pipe(ops.do(rx.Observer(on_next=lambda _: None))).run()
    assert str(actual_error.value) == 'Sequence contains no elements'


def test_when_not_all_calls_to_client_return_empty_list(mock_client):
    count = 0

    def assertion(u):
        nonlocal count
        count += 1
        assert u.id == 1

    # as long as not all calls to the client returns empty lists, it's ok
    mock_get_users_by_usernames = MagicMock(side_effect=[[], [User(id=1)]])
    mock_client.get_users_by_usernames = mock_get_users_by_usernames
    rule = NameUserSourceRule.parse_obj({'names': ['first_request'] * 100 + ['second_request']})
    rule().pipe(ops.do(rx.Observer(on_next=assertion))).run()
    assert mock_get_users_by_usernames.call_count == 2
    assert count == 1
    assert mock_get_users_by_usernames.call_args_list[1] == call(['second_request'])


def test_id_user_source_rule(mock_client):
    count = 0

    def assertion(u):
        nonlocal count
        count += 1
        assert u.id == 1

    mock_get_users_by_ids = MagicMock(side_effect=[[User(id=1)], [User(id=1)]])
    mock_client.get_users_by_ids = mock_get_users_by_ids
    rule = IdUserSourceRule.parse_obj({'ids': [1] * 100 + [2]})
    # use the Observable.run() to synchronously start and finish the pipeline.
    rule().pipe(ops.do(rx.Observer(on_next=assertion))).run()

    # the rule splits the parameter's value into two list
    # and makes two calls to the client
    assert mock_get_users_by_ids.call_count == count == 2
    assert mock_get_users_by_ids.call_args_list[0] == call([1] * 100)
    assert mock_get_users_by_ids.call_args_list[1] == call([2])
