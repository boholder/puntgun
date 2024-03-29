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

IMPROVE: More elegant way to generating a json format report file.
"""
from __future__ import annotations

import datetime
from typing import Any

import orjson
from loguru import logger

from puntgun.conf import config
from puntgun.rules.base import Plan


class Record:
    """
    Record wrapper for a recordable object for format uniformity.
    """

    def __init__(self, type: str, data: dict):
        self.type = type
        self.data = data

    def to_json(self) -> bytes:
        """Transform this record into a yaml-list-item format string"""
        return orjson.dumps({"type": self.type, "data": self.data})

    @staticmethod
    def parse_from_dict(conf: dict) -> Record:
        """
        Assume that the parameter is already a dictionary type parsed from a json file.
        """
        return Record(type=conf.get("type", ""), data=conf.get("data", {}))

    def __str__(self) -> str:
        return f"Record(type={self.type}, data={self.data})"

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, type(self)):
            type_equal = self.type == other.type
            data_equal = self.data == other.data
            return type_equal and data_equal
        else:
            return False


class Recordable:
    """Interface for objects that can be recorded into report file."""

    def to_record(self) -> Record:
        """Record the object."""
        raise NotImplementedError

    @staticmethod
    def parse_from_record(record: Record) -> Recordable:
        """Generate an instance from a record."""
        raise NotImplementedError


COMMA = b","

# 1. an empty list item (an empty map) for pairing one comma character behind the last plan item
# 2. one square bracket for closing the "plans" list
# 3. one curly bracket for closing the root level dictionary
REPORT_TAIL = b"{}]}"


class Recorder:
    """
    Saving / loading execution results with a report file in json format.
    Annoying temporal coupling included, you must call methods in this class
    at proper time and following certain order to compose a correct json format output.
    """

    @staticmethod
    def _write(msg: bytes) -> None:
        """Any else more convenient than this?"""
        # the logger filter will recognize the "r" field and output this line of log into report file.
        logger.bind(r=True).info(msg.decode("utf-8"))

    @staticmethod
    def record(recordable: Recordable) -> None:
        """
        Log recordable instances into report file as normal log.
        """
        # write as a "records" list item
        Recorder._write(recordable.to_record().to_json() + COMMA)

    @staticmethod
    def write_report_header(plans: list[Plan]) -> None:
        """
        This paragraph works as the report file content's header
        - for correctly formatting latter records in json format.
        """

        head = {
            "reference_documentation": "https://boholder.github.io/puntgun/dev//usage/report-file",
            # For version based branch logic in report-based "undo" operation.
            # (you have different available actions at different version,
            # which may require different "undo" process.)
            # Works sort of like java's serial version uid.
            "tool_version": config.tool_version,
            "generate_time": datetime.datetime.utcnow(),
            "plan_configuration": config.settings.get("plans", []),
            # name -> plan_configuration, id -> records,
            # this list sort of like a relation table.
            "plan_ids": [{"name": p.name, "id": p.id} for p in plans],
            "records": [],
        }

        Recorder._write(orjson.dumps(head, option=orjson.OPT_INDENT_2)[:-3])

    @staticmethod
    def write_report_tail() -> None:
        """
        After all records are written, at the end of the program running,
        append this part to remain a correct json format.
        """
        Recorder._write(REPORT_TAIL)


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
    #
    # lambda for lazy calculating
    cases = [
        lambda: file_content,
        # The bigger the file_content (record file size),
        # the slower the appending speed (you need to copy the whole list),
        # but thankfully this method runs only once per program running.
        lambda: file_content + REPORT_TAIL,
    ]

    errors = []
    for case in cases:
        try:
            result = orjson.loads(case())

            # remove additional empty items added by this class when writing report.
            # "records" list's last item is empty item.
            result["records"] = result["records"][:-1]

            return result
        except orjson.JSONDecodeError as e:
            errors.append(e)

    raise ValueError(f"Can not parse given content, all approaches return error: {errors}")
