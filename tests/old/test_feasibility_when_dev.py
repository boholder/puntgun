import functools
import time
import unittest
from unittest import TestCase

import reactivex as rx
from hamcrest import assert_that, equal_to
from reactivex import operators as op


class TestLibrary(TestCase):
    """Try libraries' api"""

    @unittest.skip('test for development')
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

    @unittest.skip('test for development')
    def test_rx_error_delivering(self):
        def mapper(e):
            if e == 3:
                raise AssertionError('exp')
            else:
                return e

        mix = rx.of(1, 'text', 3, 4, 'hi').pipe(op.map(mapper))

        mix.pipe(op.filter(lambda x: isinstance(x, str))) \
            .subscribe(on_next=lambda x: print(x),
                       on_error=lambda e: print('error str:', e))

        mix.pipe(op.filter(lambda x: isinstance(x, int))) \
            .subscribe(on_next=lambda x: print(x),
                       on_error=lambda e: print('error number:', e))

    @unittest.skip('test for development')
    def test_observable_emit_time(self):
        def rule1(value):
            print(f'rule 1 begin on:{value}')
            if value % 2 == 0:
                time.sleep(0.1)
            print(f'rule 1 finish on:{value}')

            return f'rule 1 first return:{value}'

        def rule2(value):
            print(f'rule 2 begin on:{value}')
            if value % 2 == 1:
                time.sleep(0.1)
            print(f'rule 2 finish on:{value}')

            return f'rule 2 first return:{value}'

        def judge_on_one_context(context):
            stream = rx.of(context)
            r1o = stream.pipe(op.map(rule1))
            r2o = stream.pipe(op.map(rule2))

            # have to manually set delay
            if context % 2 == 0:
                # rule 1 quicker at 1,3
                r1o = r1o.pipe(op.delay(1))
            else:
                # rule 1 quicker at 2
                r2o = r2o.pipe(op.delay(1))

            return r1o.pipe(op.merge(r2o)).pipe(op.first())

        # take only first result,
        # and other processing seems would never finish.
        rx.range(1, 4).pipe(
            op.map(judge_on_one_context)
        ).subscribe(lambda x: x.subscribe(lambda t: print(f'==={t}===')))

    # @unittest.skip('test for development')
    def test_rx_group_by(self):
        class A(object):
            def __init__(self, name):
                self.name = name

        class B(object):
            def __init__(self, name):
                self.name = name

        a = 1

        def assignment(grp):
            nonlocal a
            if grp.key:
                a = grp.underlying_observable
                return a
            else:
                b = grp.underlying_observable.subscribe(lambda x: print(f'b:{x.name}'))
                return b

        rx.of(A('a1'), A('a2'), B('b1'), B('b2'), A('a3'), B('b3')).pipe(
            op.group_by(lambda x: isinstance(x, A)),
        ).subscribe(assignment)
