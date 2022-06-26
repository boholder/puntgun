import pytest
from hamcrest import assert_that, is_, contains_string
from pydantic import ValidationError

from rules import NumericFilterRule


class TestNumericUserFilterRule:
    @pytest.fixture
    def rule(self):
        return lambda obj: NumericFilterRule.parse_obj(obj)

    def test_check_number_order(self, rule):
        with pytest.raises(ValidationError) as actual_error:
            rule({'more_than': 10, 'less_than': 5})
        assert_that(str(actual_error.value), contains_string('than'))

    def test_single_less_than(self, rule):
        r = rule({'less_than': 10})
        assert_that(r.compare(5), is_(True))
        assert_that(r.compare(20), is_(False))

    def test_single_more_than(self, rule):
        r = rule({'more_than': 10})
        assert_that(r.compare(20), is_(True))
        assert_that(r.compare(5), is_(False))

    def test_both_less_more(self, rule):
        r = rule({'less_than': 20, 'more_than': 10})
        assert_that(r.compare(15), is_(True))
        assert_that(r.compare(5), is_(False))
        assert_that(r.compare(25), is_(False))
        # edge case (equal) result in False.
        assert_that(r.compare(10), is_(False))
        assert_that(r.compare(20), is_(False))
