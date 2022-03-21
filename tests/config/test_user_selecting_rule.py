import functools
import unittest
from unittest import TestCase

from hamcrest import assert_that, instance_of

from puntgun.config.user_selecting_rule import WhoField, UserSelectingRule


class TestAbstractWhoField(TestCase):
    def test_get_instance_via_config(self):
        class TestWhoField(WhoField):
            is_init_by_class_attr = True
            config_keyword = "test-key"
            expect_type = str

            def __init__(self, raw_config_value):
                super().__init__()
                self.v = raw_config_value

            def query(self, _):
                return self.v

        field = WhoField.get_instance_via_config({"test-key": "text"})
        assert_that(isinstance(field, TestWhoField))
        assert_that(field.v, instance_of(str))
        assert_that(field.v, "text")

        user_selecting_rule = UserSelectingRule({"who": {"test-key": "text"}})
        assert_that(user_selecting_rule.who, instance_of(TestWhoField))
        assert_that(user_selecting_rule.who.v, "text")

    @unittest.skip("test feasibility when developing")
    def test_inherit_cache(self):
        class A:
            def real_func(self):
                return self.template()

            @functools.lru_cache(maxsize=1)
            def template(self):
                raise NotImplementedError

        class B(A):
            @functools.lru_cache(maxsize=1)
            def template(self):
                return "B"

        class C(A):
            @functools.lru_cache(maxsize=1)
            def template(self):
                return "C"

        b = B()
        c = C()
        for _ in range(10):
            b.real_func()
            c.real_func()

        print(A.template.cache_info())
        print(B.template.cache_info())
        print(C.template.cache_info())
