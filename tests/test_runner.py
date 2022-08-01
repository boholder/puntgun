from typing import List, ClassVar

import pytest
import reactivex as rx
from reactivex import Observable
from reactivex import operators as op

from record import Recordable, Record
from rules import Plan, FromConfig
from runner import parse_plans


@pytest.fixture(autouse=True)
def mock_plan_configuration(mock_configuration):
    mock_configuration({'plans': [
        {'runner_test_plan': {'rules': [
            {'runner_test_rule': {'f': 1}},
            {'runner_test_rule': {'f': 2}}
        ]}}
    ]})


def test_parse_plans_success():
    plans = parse_plans()
    print(plans)


class TResult(Recordable):

    def __init__(self, v):
        self.v = v

    def to_record(self) -> Record:
        return Record(name='record', data={'v': self.v})

    @staticmethod
    def parse_from_record(record: Record):
        pass


class TRule(FromConfig):
    _keyword: ClassVar[str] = 'runner_test_rule'

    f: int


class TPlan(Plan):
    _keyword: ClassVar[str] = 'runner_test_plan'

    rules: List[TRule]

    def __call__(self) -> Observable[TResult]:
        return rx.from_iterable([r.f for r in self.rules]).pipe(op.map(lambda i: TResult(i)))
