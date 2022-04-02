import functools
import unittest
from unittest import TestCase

import reactivex as rx
from hamcrest import assert_that, equal_to
from reactivex import operators as op


class TestLibrary(TestCase):
    """Try libraries' api"""

    @unittest.skip("test for development")
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

    @unittest.skip("test for development")
    def test_rx_error_delivering(self):
        def mapper(e):
            if e == 3:
                raise AssertionError("exp")
            else:
                return e

        mix = rx.of(1, "text", 3, 4, "hi").pipe(op.map(mapper))

        mix.pipe(op.filter(lambda x: isinstance(x, str))) \
            .subscribe(on_next=lambda x: print(x),
                       on_error=lambda e: print("error str:", e))

        mix.pipe(op.filter(lambda x: isinstance(x, int))) \
            .subscribe(on_next=lambda x: print(x),
                       on_error=lambda e: print("error number:", e))
