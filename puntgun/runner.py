"""
Plans runner at the highest abstraction level of the tool.
Constructing plans, executing plans, collecting and recording plan results...
"""
import sys
from typing import List

import reactivex as rx
from loguru import logger
from reactivex import operators as op

from conf import config
from record import Recordable, Recorder
from rules import Plan
from rules.config_parser import ConfigParser


def start():
    execute_plans(parse_plans())


def parse_plans():
    # Let the ConfigParser recursively constructing plan instances and rule instances inside plans.
    plans: List[Plan] = [ConfigParser.parse(p, Plan) for p in config.settings.get('plans')]

    if ConfigParser.errors():
        _errors = '\n'.join([str(e) for e in ConfigParser.errors()])
        # TODO plan config reference document URL
        logger.bind(o=True).info(f"""
Found syntax errors when parsing plan configurations, will exit.
Please fix these errors in plan configuration file with configuration reference document:
Plan config file path: {config.plan_file}
Reference document: {'fake-doc'}
Syntax errors:
{_errors}
""")
        # Can't continue without a zero-error plan configuration
        raise ValueError("Found errors in plan configuration, can not continue")

    logger.info('Parsed plans from configuration: {}', plans)
    return plans


@logger.catch(onerror=lambda _: sys.exit(1))
def execute_plans(plans: List[Plan]):
    # Temporal coupling for compose a correct json format output.
    Recorder.write_report_header(plans)

    for plan in plans:
        logger.info('Begin to execute plan: {}', plan)
        # Explicitly blocking execute plans one by one.
        # for avoiding competition among plans on limited API invocation resources.
        plan().pipe(op.do(rx.Observer(on_next=process_plan_result))).run()
        logger.info('Finished plan: {}', plan)

    Recorder.write_report_tail()


def process_plan_result(result: Recordable):
    logger.bind(o=True).info('One has been operated: {}', result.to_record())
    Recorder.record(result)
