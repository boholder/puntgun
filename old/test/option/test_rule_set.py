from unittest import TestCase

from hamcrest import assert_that, calling, equal_to, instance_of, raises

from old.test import SearchFilterRule, weightOfRuleSet


class TestweightOfRuleSet(TestCase):
    def test_check_goal_not_bigger_than_weight_sum(self):
        assert_that(
            calling(weightOfRuleSet).with_args(
                [{"goal": 10}, {"condition": {"weight": 1, "search_query": "query_string"}}]
            ),
            raises(AssertionError, pattern="must be greater than the goal"),
        )

    def test_condition_config_leak_of_rule(self):
        assert_that(
            calling(weightOfRuleSet).with_args([{"goal": 1}, {"condition": {"weight": 1}}]),
            raises(AssertionError, pattern="must have exact one filter option"),
        )

    def test_normal_build(self):
        weight_of_rule_set = weightOfRuleSet(
            [
                {"goal": 1},
                {"condition": {"weight": 1, "search_query": "query_string"}},
                {"condition": {"weight": 1, "search_query": "query_string2"}},
            ]
        )
        assert_that(weight_of_rule_set.goal, equal_to(1))
        assert_that(len(weight_of_rule_set.condition), equal_to(2))

        assert_that(weight_of_rule_set.condition[0].weight, equal_to(1))
        assert_that(weight_of_rule_set.condition[0].rule, instance_of(SearchFilterRule))
        assert_that(weight_of_rule_set.condition[0].rule.query, equal_to("query_string"))

        assert_that(weight_of_rule_set.condition[1].weight, equal_to(1))
        assert_that(weight_of_rule_set.condition[1].rule, instance_of(SearchFilterRule))
        assert_that(weight_of_rule_set.condition[1].rule.query, equal_to("query_string2"))
