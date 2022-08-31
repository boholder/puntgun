from unittest import TestCase

from hamcrest import assert_that, equal_to

from old.test import SearchFilterRule, SearchQueryFilterRule


class TestSearchFilterRule(TestCase):
    def test_build_one(self):
        rule = SearchFilterRule.build({"name": "option!", "query": "q_text"})
        assert_that(rule.name, equal_to("option!"))
        assert_that(rule.work_count, equal_to(100))
        assert_that(rule.query, equal_to("q_text"))


class TestSearchQueryFilterRule(TestCase):
    def test_build_one(self):
        rule = SearchQueryFilterRule.build("q_text")
        assert_that(rule.work_count, equal_to(100))
        assert_that(rule.query, equal_to("q_text"))
