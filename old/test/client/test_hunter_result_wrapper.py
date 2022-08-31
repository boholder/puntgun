from unittest import TestCase

import reactivex as rx
from hamcrest import assert_that, is_
from reactivex import operators as op

from old.test import MixedResultProcessingWrapper
from old.test import TwitterApiError


class TestHunterResultWrapper(TestCase):
    def test_model_consume(self):
        build_test_data().pipe_on_model(op.map(lambda x: x + 1), op.map(lambda x: f"{x}a")).subscribe_on_model(
            lambda x: assert_that(x, is_("2a"))
        ).wire()

    def test_error_consume(self):
        build_test_data().pipe_on_error(op.map(lambda x: x.title), op.map(lambda x: f"{x}_a")).subscribe_on_error(
            lambda x: assert_that(x, is_("title_a"))
        ).wire()


def build_test_data():
    return MixedResultProcessingWrapper(rx.of(1, TwitterApiError("title", "url", "detail", "param", "value")))
