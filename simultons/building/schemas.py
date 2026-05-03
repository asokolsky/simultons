"""
Schemas for the REST APIs inputs and outputs
"""

from enum import auto
from typing import Union

from fastapi_utils.enums import StrEnum
from pydantic import BaseModel, NonNegativeInt, PositiveInt

from simultons.schemas import ClockResponse


class ElevatorState(StrEnum):
    """
    Possible values of the Elevator State
    """

    # low power state for an empty elevator with closed doors
    IDLE = auto()
    # with or without load
    DOORS_OPENING = auto()
    # with or without load
    DOORS_CLOSING = auto()
    # moving to a destination floor with or without load
    GOING = auto()
    # with or without load
    DOORS_OPENED = auto()

    @classmethod
    def is_valid(cls, st: Union[str, 'ElevatorState']) -> bool:
        """
        Valid value recognizer
        """
        return st in ElevatorState._value2member_map_

    def __repr__(self) -> str:
        """
        To enable serialization as a string...
        """
        return repr(self.value)


class NewElevatorParams(BaseModel):
    """
    JSON used to create a new elevator
    """

    name: str
    floors: PositiveInt


class ElevatorResponse(ClockResponse):
    """
    JSON describing the elevator in the body of the HTTP response
    """

    state: ElevatorState
    current_floor: NonNegativeInt
    floors: PositiveInt
