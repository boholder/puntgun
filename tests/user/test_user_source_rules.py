from unittest.mock import MagicMock, call

import pytest
import reactivex as rx
import reactivex.operators as ops

import client
from user import User
from user.source_rules import NameUserSourceRule


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
    rule(mock_client).pipe(ops.do(rx.Observer(on_next=assertion))).run()

    # the rule splits the parameter's value into two list
    # and makes two calls to the client
    assert mock_get_users_by_usernames.call_count == count == 2
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
        rule(mock_client).pipe(ops.do(rx.Observer(on_error=assertion_consumer))).run()

    assert str(actual_error.value) == 'error'


@pytest.fixture
def mock_client(monkeypatch):
    c = MagicMock()
    monkeypatch.setattr(client.Client, 'singleton', lambda: c)
    return c
