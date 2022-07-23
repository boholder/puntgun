import datetime

import orjson
from loguru import logger


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
        return orjson.dumps({'type': self.name, 'time': datetime.datetime.now(), 'data': self.data}).decode('utf-8')

    @staticmethod
    def from_parsed_dict(config: dict):
        """
        Assume that the parameter is already a dictionary type parsed from a json file.
        """
        return Record(config.get('type', ''), config.get('data', {}))


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
    """Saving things to a report file in a human-readable format."""

    @staticmethod
    def record(recordable: Recordable):
        """"""
        logger.info()
       