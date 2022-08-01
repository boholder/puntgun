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
    # Let the ConfigParser recursively constructing plan instances (and rule instances inside plans).
    plans = [ConfigParser.parse(p, Plan) for p in config.settings.get('plans', [])]

    if ConfigParser.errors():
        _errors = '\n'.join(ConfigParser.errors())
        logger.bind(o=True).info(f"""
Found syntax errors when parsing plan configurations, will exit.
Please fix these errors in plan configuration file with configuration reference document:
Plan config file path: {config.plan_file}
Document: {''}
Syntax errors: 
{_errors}
""")

    logger.info('Successfully parsed plans from configuration without errors: {}', plans)
    return plans


@logger.catch(onerror=lambda _: sys.exit(1))
def execute_plans(plans: List[Plan]):
    # Temporal coupling for compose a correct json format output.
    Recorder.write_report_header(plans)

    for plan in plans:
        logger.info('Begin to execute plan: {}', plan)
        # Explicitly blocking execute plans one by one.
        # for avoiding limited API invocation resources competition.
        plan().pipe(op.do(rx.Observer(on_next=process_plan_result))).run()
        logger.info('Successfully finished plan: {}', plan)

    Recorder.write_report_tail()


def process_plan_result(result: Recordable):
    logger.bind(o=True).info('One candidate triggers filters and has been operated: {}', result)
    Recorder.record(result)
