from typing import ClassVar, List

import pytest
import reactivex as rx
from hamcrest import assert_that, contains_inanyorder, contains_string
from reactivex import Observable
from reactivex import operators as op

from puntgun import runner
from puntgun.record import Record, Recordable, load_report
from puntgun.rules.base import FromConfig, Plan
from puntgun.rules.config_parser import ConfigParser


@pytest.fixture
def mock_plan_configuration(mock_configuration):
    mock_configuration(
        {
            "plans": [
                {"runner_test_plan": {"rules": [{"runner_test_rule": {"f": 0}}, {"runner_test_rule": {"f": 1}}]}},
                {"runner_test_plan": {"rules": [{"runner_test_rule": {"f": 2}}, {"runner_test_rule": {"f": 3}}]}},
            ]
        }
    )


def test_parse_plans_success(mock_plan_configuration):
    actual_plans = runner.parse_plans_config(runner.get_and_validate_plan_config())
    assert actual_plans[0].rules == [TRule(f=0), TRule(f=1)]
    assert actual_plans[1].rules == [TRule(f=2), TRule(f=3)]


def test_parse_plans_fail(mock_configuration, clean_config_parser_errors):
    mock_configuration({"plans": [{"cause": "error"}]})

    with pytest.raises(ValueError) as e:
        runner.parse_plans_config(runner.get_and_validate_plan_config())

    assert_that(str(e), contains_string("plan configuration"))
    assert len(ConfigParser.errors()) == 1
    assert_that(str(ConfigParser.errors()[0]), contains_string("cause"))


def test_execute_success(mock_record_logger, mock_plan_configuration):
    runner.execute_plans(runner.parse_plans_config(runner.get_and_validate_plan_config()))
    records_in_report = load_report(mock_record_logger.get_content()).get("records")
    assert_that(records_in_report, contains_inanyorder(*[{"type": "tr", "data": {"v": i}} for i in range(4)]))


class TResult(Recordable):
    def __init__(self, v):
        self.v = v

    def to_record(self) -> Record:
        return Record(type="tr", data={"v": self.v})

    @staticmethod
    def parse_from_record(record: Record):
        pass


class TRule(FromConfig):
    _keyword: ClassVar[str] = "runner_test_rule"

    f: int


class TPlan(Plan):
    _keyword: ClassVar[str] = "runner_test_plan"

    rules: List[FromConfig]

    def __call__(self) -> Observable[TResult]:
        return rx.from_iterable([r.f for r in self.rules]).pipe(op.map(lambda i: TResult(i)))

    @classmethod
    def parse_from_config(cls, conf: dict):
        return cls(rules=[ConfigParser.parse(c, FromConfig) for c in conf[cls._keyword]["rules"]])
