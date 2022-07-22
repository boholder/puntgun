import datetime

import yaml


class Record(object):
    """
    Record wrapper for a recordable object for format uniformity.
    """
    name: str
    data: dict

    def __init__(self, name: str, data: dict):
        self.name = name
        self.data = data

    def to_yaml(self) -> str:
        """
        Translate this record into a yaml-list-item format string.
        "time" field for labeling record happening time.
        Remove first line of placeholder (3 chars - "a:\n") for creating a "list-item".
        """
        return yaml.safe_dump({'a': [{'type': self.name, 'time': datetime.datetime.now(), 'data': self.data}]})[3::]

    @staticmethod
    def from_parsed_yaml(config: dict):
        """
        Assume that the parameter is a python dictionary type parsed from yaml file by dynaconf or pyyaml.
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
        pass
