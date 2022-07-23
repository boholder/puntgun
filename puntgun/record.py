"""
Saving / loading execution results, errors with a report file in **json** format.
This report file can give user a clean view what had been done in last run.

First time I intended to output the record as yaml or toml format,
because these two format aren't require back-closure-symbols like json's brackets.
Then I can output records to file with logger as normal log,
whenever the program exits the whole file remains parsable,
and the output is more clean and has less useless single-brackets lines.

Then I found this question:
https://stackoverflow.com/questions/27743711/can-i-speedup-yaml
in which answers point out that yaml parsing (loading) in python is pretty slow.

Ok, speed is important. I changed the output format to json -
I've heard about the effort different json parsing libraries have made.
"""
import datetime

import orjson
from loguru import logger

from conf import config
from rules import Plan

REPORT_HEAD = {'referring_document': '',  # TODO
               'tool_version': config.puntgun_version,
               'generate_time': datetime.datetime.now(),
               # contains detail records:
               #
               # 'plans': [
               # {'name': '...',
               # 'records': [...]
               # },
               # ...
               # ]
               'plans': []}

# 1. an empty list item (an empty map) for pairing one comma character behind the last item
# (TODO gonna remo this empty list item while parsing)
# 2. one square bracket for closing the "records" list
# 3. one curly bracket for closing the plan list item
PLAN_RECORD_TAIL = '{}]}'

# 1. one square bracket for closing the "plans" list
# 2. one curly bracket for closing the root level dictionary
REPORT_TAIL = ']}'


class Record(object):
    """
    Record wrapper for a recordable object for format uniformity.
    """
    name: str
    data: dict

    def __init__(self, name: str, data: dict):
        self.name = name
        self.data = data

    def to_json(self) -> str:
        """
        Translate this record into a yaml-list-item format string.
        "time" field for labeling record happening time.
        """
        return orjson.dumps({'type': self.name, 'time': datetime.datetime.now(), 'data': self.data}).decode('utf-8')

    @staticmethod
    def from_parsed_dict(conf: dict):
        """
        Assume that the parameter is already a dictionary type parsed from a json file.
        """
        return Record(conf.get('type', ''), conf.get('data', {}))


class Recordable(object):
    """Interface for objects that can be recorded into report file."""

    def to_record(self) -> Record:
        """Record the object."""
        raise NotImplementedError

    @staticmethod
    def parse_from_record(record: Record):
        """Generate an instance from a record."""
        raise NotImplementedError


class Recorder(object):
    """
    Saving / loading execution results with a report file in json format.
    Annoying temporal coupling included, you must call methods in this class
    at proper time and following certain order.
    """

    @staticmethod
    def record(recordable: Recordable):
        """
        Log recordable instances into report file as normal log.
        """
        logger.info(recordable.to_record().to_json() + ',')

    @staticmethod
    def write_report_header():
        """
        This paragraph works as the report file content's header
        - for correctly formatting latter records in json format.
        """
        logger.info(orjson.dumps(REPORT_HEAD, option=orjson.OPT_INDENT_2)[:-2])

    @staticmethod
    def write_report_tail():
        """
        After all records are written, at the end of the program running,
        append this part to remain a corrct json format.
        """
        logger.info(REPORT_TAIL)

    @staticmethod
    def write_plan_record_header(plan: Plan):
        """Call it before running every plan."""
        logger.info(orjson.dumps({'name': plan.name, 'records': []}, option=orjson.OPT_INDENT_2)[:-2])

    @staticmethod
    def write_plan_record_tail():
        """Call it after a plan running finish."""
        logger.info(PLAN_RECORD_TAIL)

    @staticmethod
    def load_report(file_content: bytes) -> dict:
        """
        Load report into dictionary type from given report file.
        Responsible to handle json-special format problems.
        """

        # If the program finished its job and stopped by itself,
        # correct brackets will be appended at the tail of file,
        # it's json-format-correct.
        #
        # But if the program stopped by user, unexpected exceptions...
        # the file's content is json-format-broken,
        # we'll fix it manually as we know what it's missing.
        cases = [lambda: file_content,
                 lambda: file_content + REPORT_TAIL.encode('utf-8'),
                 lambda: file_content + (PLAN_RECORD_TAIL + REPORT_TAIL).encode('utf-8')]

        errors = []
        for case in cases:
            try:
                return orjson.loads(case())
            except orjson.JSONDecodeError as e:
                errors.append(e)

        raise ValueError(f'Can not parse given content, all three approaches return error: {errors}')
