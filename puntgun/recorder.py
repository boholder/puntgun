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
        # TODO untested

        return f"""
  - type: {self.type}
    time: {datetime.now()}
    data: 
{[f'      - {k}: {v}' for k, v in self.data]}
"""


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
