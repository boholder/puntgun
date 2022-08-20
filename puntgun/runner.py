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
def start():
    # the "exclude" option of @logger.catch won't stop outputting stack trace
    try:
        plans = parse_plans_config(get_and_validate_plan_config())
        logger.info('Parsed plans: {}', plans)
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


def get_and_validate_plan_config():
    plans_config = config.settings.get('plans')
    if plans_config is None:
        print(NO_PLAN_LOAD.format(plan_file=config.plan_file))
        raise InvalidConfigurationError('No plan is loaded')
    return plans_config


# TODO doc link
# copy the format from Prometheus's promtool
CHECK_PLAN_FAIL = """Checking {plan_file} FAIL,
Please fix these errors in plan configuration file with reference document.
Reference documentation: 
fake-doc
Errors:
{errors}"""

CHECK_PLAN_SUCC = """Checking {plan_file} SUCCESS,
{plan_num} plans found."""


def parse_plans_config(_plans_config):
    """Let the ConfigParser recursively constructing plan instances and rule instances inside plans."""
    plans: List[Plan] = [ConfigParser.parse(p, Plan) for p in _plans_config]

    # Can't continue without a zero-error plan configuration
    if ConfigParser.errors():
        errors = '\n'.join([str(e) for e in ConfigParser.errors()])
        print(CHECK_PLAN_FAIL.format(plan_file=config.plan_file, errors=errors))
        raise InvalidConfigurationError("Found errors in plan configuration")

    print(CHECK_PLAN_SUCC.format(plan_file=config.plan_file, plan_num=len(plans)))
    return plans


# calculate number of CPUs, then create a ThreadPoolScheduler with that number of threads
optimal_thread_count = multiprocessing.cpu_count()
pool_scheduler = ThreadPoolScheduler(optimal_thread_count)


def execute_plans(plans: List[Plan]):
    # Temporal coupling for compose a correct json format output.
    Recorder.write_report_header(plans)

    for plan in plans:
        logger.info('Begin to execute plan: {}', plan)
        # Explicitly blocking execute plans one by one.
        # for avoiding competition among plans on limited API invocation resources.
        plan().pipe(op.subscribe_on(pool_scheduler),
                    op.do(rx.Observer(on_next=process_plan_result))
                    ).run()
        logger.info('Finished plan: {}', plan)

    Recorder.write_report_tail()


def process_plan_result(result: Recordable):
    logger.bind(o=True).info('Finished actions on one target: {}', result.to_record())
    Recorder.record(result)
