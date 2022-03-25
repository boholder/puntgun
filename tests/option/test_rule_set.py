from unittest import TestCase

from hamcrest import assert_that, calling, raises, equal_to, instance_of

from puntgun.option.filter_rule import SearchFilterRule
from puntgun.option.rule_set import WightOfRuleSet


class TestWightOfRuleSet(TestCase):
    def test_check_goal_not_bigger_than_wight_sum(self):
        assert_that(calling(WightOfRuleSet)
                    .with_args([{'goal': 10},
                                {'condition': {'wight': 1, 'search-query': 'query-string'}}]),
                    raises(AssertionError, pattern="must be greater than the goal"))

    def test_condition_config_leak_of_rule(self):
        assert_that(calling(WightOfRuleSet)
                    .with_args([{'goal': 1},
                                {'condition': {'wight': 1}}]),
                    raises(AssertionError, pattern="must have exact one filter option"))

    def test_normal_build(self):
        wight_of_rule_set = WightOfRuleSet([{'goal': 1},
                                            {'condition': {'wight': 1, 'search-query': 'query-string'}},
                                            {'condition': {'wight': 1, 'search-query': 'query-string2'}}])
        assert_that(wight_of_rule_set.goal, equal_to(1))
        assert_that(len(wight_of_rule_set.condition), equal_to(2))

        assert_that(wight_of_rule_set.condition[0].wight, equal_to(1))
        assert_that(wight_of_rule_set.condition[0].rule, instance_of(SearchFilterRule))
        assert_that(wight_of_rule_set.condition[0].rule.query, equal_to('query-string'))

        assert_that(wight_of_rule_set.condition[1].wight, equal_to(1))
        assert_that(wight_of_rule_set.condition[1].rule, instance_of(SearchFilterRule))
        assert_that(wight_of_rule_set.condition[1].rule.query, equal_to('query-string2'))
