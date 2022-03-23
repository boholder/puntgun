from unittest import TestCase

from hamcrest import assert_that, equal_to

from puntgun.config.filter_rule import SearchFilterRule, SearchQueryFilterRule


class TestSearchFilterRule(TestCase):
    def test_build_one(self):
        rule = SearchFilterRule.build({'name': 'rule!', 'query': 'q-text'})
        assert_that(rule.name, equal_to('rule!'))
        assert_that(rule.count, equal_to(100))
        assert_that(rule.query, equal_to('q-text'))


class TestSearchQueryFilterRule(TestCase):
    def test_build_one(self):
        rule = SearchQueryFilterRule.build('q-text')
        assert_that(rule.count, equal_to(100))
        assert_that(rule.query, equal_to('q-text'))
