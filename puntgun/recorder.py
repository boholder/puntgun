from datetime import datetime

from pydantic import BaseModel


class Record(BaseModel):
    """
    Record wrapper for a recordable object for format uniformity.
    """
    type: str
    data: dict

    def to_yaml(self) -> str:
        """
        Translate this record into a yaml-list-item format string.
        "time" field for labeling record happening time.
        """

        # first line is only '\n'
        data_list = '\n'.join([f'      - {k}: {v}' for k, v in self.data.items()])

        # <an empty line for spacing>
        #  - type: <type>
        #    time: <time>
        #    data:
        #      - a: ...
        #      - b: ...
        #      ...
        # <no empty line at bottom>
        return f"""
  - type: {self.type}
    time: {datetime.now()}
    data:
{data_list}"""

    @staticmethod
    def from_parsed_yaml(config: dict):
        """
        I don't want to add pyyaml package for parsing yaml, let the dynaconf do it.
        So assume that the parameter is a python dictionary parsed from yaml file by dynaconf.
        """
        return Record(type=config['type'], data=config['data'])


class Recordable(object):
    """Interface for objects that can be recorded into report file."""

    def record(self) -> Record:
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
