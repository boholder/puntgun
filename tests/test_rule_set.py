from unittest import TestCase

from hamcrest import assert_that, calling, raises

from puntgun.config.rule_set import RuleSet


class TestRuleSet(TestCase):
    def test_name_field_number_check(self):
        assert_that(calling(RuleSet).with_args([{'name': 'name1'}, {'name': 'name2'}]),
                    raises(AssertionError, pattern="one name field"))


class TestWightOfRuleSet(TestCase):
    # TODO 补全测试
    pass
