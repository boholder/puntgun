"""
Plans runner at the highest abstraction level of the tool.
Constructing plans, executing plans, collecting and recording plan results...
"""
import multiprocessing
import sys
from typing import List

import reactivex as rx
from loguru import logger
from reactivex import operators as op
from reactivex.scheduler import ThreadPoolScheduler

from puntgun.client import Client
from puntgun.conf import config
from puntgun.record import Recordable, Recorder
from puntgun.rules import Plan
from puntgun.rules.config_parser import ConfigParser


class InvalidConfigurationError(ValueError):
    """
    Need a "checked" (already know will be raised) error type to terminate the tool,
    without be caught by loguru and print a lot of meaningless dialog stack trace to stderr
    (it will make the user confused).
    """

    pass


@logger.catch(onerror=lambda _: sys.exit(1))
def start() -> None:
    # Warm up? Initialization?
    # Load secrets and create singleton client instance before parsing and executing plans.
    #
    # I found that after the reactivex pipeline (plan execution) is started,
    # user can't exit the program by pressing "Ctrl+C" easily.
    # And there is no "os._exit()" in os module if I want to exit in sub-thread:
    # https://stackoverflow.com/questions/1489669/how-to-exit-the-entire-application-from-a-python-thread
    Client.singleton()

    # the "exclude" option of @logger.catch won't stop outputting stack trace
    try:
        plans = parse_plans_config(get_and_validate_plan_config())
        logger.info("Parsed plans: {}", plans)
        execute_plans(plans)
    except InvalidConfigurationError:
        exit(1)


# TODO doc link
NO_PLAN_LOAD = """No plan is loaded.
The tool is trying to load from this plan configuration file:
{plan_file}
If it not exists, generate example configuration files with "puntgun gen config".
If it exists, check if its content is valid with "puntgun check plan --plan_file=...",
and fix it with reference documentation:
fake-doc """


def get_and_validate_plan_config() -> list[dict]:
    plans_config = config.settings.get("plans")
    if plans_config is None:
        print(NO_PLAN_LOAD.format(plan_file=config.plan_file))
        raise InvalidConfigurationError("No plan is loaded")
    return plans_config


# TODO doc link
# copy the format from Prometheus's "promtool" command lint tool
# https://prometheus.io/docs/prometheus/latest/configuration/unit_testing_rules/
CHECK_PLAN_FAIL = """Checking {plan_file} FAIL,
Please fix these errors in plan configuration file with reference document.
Reference documentation:
fake-doc
Errors:
{errors}"""

CHECK_PLAN_SUCC = """Checking {plan_file} SUCCESS,
{plan_num} plans found."""


def parse_plans_config(_plans_config: list[dict]) -> List[Plan]:
    """Let the ConfigParser recursively constructing plan instances and rule instances inside plans."""
    plans: List[Plan] = [ConfigParser.parse(p, Plan) for p in _plans_config]

    # Can't continue without a zero-error plan configuration
    if ConfigParser.errors():
        errors = "\n".join([str(e) for e in ConfigParser.errors()])
        print(CHECK_PLAN_FAIL.format(plan_file=config.plan_file, errors=errors))
        raise InvalidConfigurationError("Found errors in plan configuration")

    print(CHECK_PLAN_SUCC.format(plan_file=config.plan_file, plan_num=len(plans)))
    return plans


# calculate number of CPUs, then create a ThreadPoolScheduler with that number of threads
optimal_thread_count = multiprocessing.cpu_count()
pool_scheduler = ThreadPoolScheduler(optimal_thread_count)


def execute_plans(plans: List[Plan]) -> None:
    def on_error(e: Exception) -> None:
        logger.error("Error occurred when executing plan", e)
        raise e

    def run_plans() -> None:
        for plan in plans:
            logger.info("Plan[id={}] start", plan.id)

            try:
                # Explicitly blocking execute plans one by one.
                # for avoiding competition among plans on limited API invocation resources.
                plan().pipe(
                    op.subscribe_on(pool_scheduler), op.do(rx.Observer(on_next=process_plan_result, on_error=on_error))
                ).run()
            except rx.internal.SequenceContainsNoElementsError:
                # If there is no element in the pipeline, the reactivex library will raise an error,
                # catch this error as an expected case.
                logger.warning("Plan[id={}] has no valid target (no candidate triggered filter rules)", plan.id)

            logger.info("Plan[id={}] finished", plan.id)

    # Temporal coupling for compose a correct json format report.
    Recorder.write_report_header(plans)
    run_plans()
    Recorder.write_report_tail()


def process_plan_result(result: Recordable) -> None:
    logger.bind(o=True).info("Finished actions on one target: {}", result.to_record())
    Recorder.record(result)
