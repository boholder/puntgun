from typing import Generic, TypeVar

from pydantic import BaseModel


class Recordable(object):
    """Interface for objects that can be recorded into report file."""

    def record(self) -> str:
        """Record the object."""
        raise NotImplementedError


_T = TypeVar('_T', bound=Recordable)


class Record(Generic[_T], BaseModel):
    """
    Record wrapper for a recordable object.
    Handling basic output formatting for format uniformity.
    """
    pass


class Recorder(object):
    """Saving things to a report file in a human-readable format."""

    @staticmethod
    def record(recordable: Recordable):
        """"""
        pass
