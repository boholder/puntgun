import pytest
import reactivex as rx
from hamcrest import assert_that, contains_string, all_of

from rules import Plan
from rules.config_parser import ConfigParser
from rules.user import User
from rules.user.filter_rules import UserFilterRule
from rules.user.source_rules import UserSourceRule


class TAnotherUserSourceRule(UserSourceRule):
    _keyword = 'psr'
    num: int

    def __call__(self):
        return rx.from_iterable([User(id=i) for i in range(self.num)])


class TOddTriggerUserFilterRule(UserFilterRule):
    _keyword = "otf"

    def __call__(self, user: User):
        return user.id % 1 == 0


@pytest.fixture
def zipped_result_checker():
    """Use with TOddTriggerUserFilterRule"""

    call_count = 0

    def check_result(zipped_user_bool):
        nonlocal call_count
        # [0] is a user instance
        assert zipped_user_bool[0].id == call_count
        # [1] is filter result of this user
        assert zipped_user_bool[1] == call_count % 1 == 0
        call_count += 1
        check_result.call_count = call_count

    return check_result


def test_required_fields_validation(clean_config_parser):
    ConfigParser.parse({'user_plan': ''}, Plan)
    error = ConfigParser.errors()[0]
    # the error message looks like:
    assert_that(str(error), all_of(contains_string('required'),
                                   contains_string('from'),
                                   contains_string('do')))


# def test_filtering_with_filter_rule():
#     plan = ConfigParser.parse({'user_plan': 'plan name',
#                                'from': [{'psr': {'num': 3}}],
#                                'that': [{'otf': {}}],
#                                'do': []}, Plan)
#
#     assert plan.name == 'plan name'
#
#     plan.filtering().pipe(op.do(rx.Observer(on_next=zipped_result_checker))).run()
#     assert zipped_result_checker.call_count == 3


def test_filtering_without_filter_rule():
    pass
