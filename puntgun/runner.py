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

from conf import config
from record import Recordable, Recorder
from rules import Plan
from rules.config_parser import ConfigParser


@logger.catch(onerror=lambda _: sys.exit(1))
def start():
    execute_plans(parse_plans())


def parse_plans():
    """Let the ConfigParser recursively constructing plan instances and rule instances inside plans."""

    def get_and_validate_plan_config():
        plans_config = config.settings.get('plans')
        if plans_config is None:
            # TODO doc link
            logger.bind(o=True).error(f"""
No plan is loaded.
The tool is trying to load from this plan configuration file:
{config.plan_file}
Check if its content is valid by running "puntgun check plan --plan_file=...",
and fix it with reference documentation:
fake-doc 
""")
            raise ValueError
        return plans_config

    def parse_plans_config(_plans_config):
        plans: List[Plan] = [ConfigParser.parse(p, Plan) for p in _plans_config]

        # Can't continue without a zero-error plan configuration
        if ConfigParser.errors():
            _errors = '\n'.join([str(e) for e in ConfigParser.errors()])
            # TODO doc link
            logger.bind(o=True).error(f"""
Checking {config.plan_file} FAIL,
Please fix these errors in plan configuration file with reference document.
Reference documentation: 
fake-doc
Errors:
{_errors}
""")
            raise ValueError("Found errors in plan configuration, can not continue")

        return plans

    plans = parse_plans_config(get_and_validate_plan_config())

    logger.bind(o=True).info(f"""
Checking {config.plan_file} SUCCESS,
{len(plans)} plans found.
""")
    logger.info('Parsed plans: {}', plans)

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
