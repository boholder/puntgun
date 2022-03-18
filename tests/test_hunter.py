import functools
import unittest
from unittest import TestCase

from hamcrest import assert_that, equal_to

from puntgun.hunter import Hunter


class TestHunter(TestCase):
    @unittest.skip("test feasibility when developing")
    def test_singleton_instance(self):
        class TestHunterClass(object):
            @staticmethod
            @functools.cache
            def get_instance():
                return 1

        for _ in range(10):
            TestHunterClass.get_instance()
        cache_info = TestHunterClass.get_instance.cache_info()
        assert_that(cache_info.misses, equal_to(1))
        assert_that(cache_info.hits, equal_to(9))
        assert_that(cache_info.currsize, equal_to(1))
