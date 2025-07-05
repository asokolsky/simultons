"""
Schemas for the REST APIs inputs and outputs
"""

from enum import auto

from fastapi_utils.enums import StrEnum
from pydantic import BaseModel, PositiveInt


class NewClockParams(BaseModel):
    """
    JSON describing new clock
    """

    name: str


class ClockResponse(BaseModel):
    """
    JSON describing simulation state
    """

    id: str
    name: str
    time: float


class NewElevatorParams(BaseModel):
    """
    JSON used to create a new elevator
    """

    name: str
    floors: PositiveInt


class ElevatorResponse(BaseModel):
    """
    JSON describing the elevator in the body of the HTTP response
    """

    id: str
    name: str
    floors: PositiveInt


class Message(BaseModel):
    """
    JSON carrying a single message in the body of the HTTP response
    """

    message: str

    def __init__(self, message: str) -> None:
        super().__init__(message=message)
        return


class SimulationState(StrEnum):
    """
    Possible values of the simulation state
    """

    INIT = auto()
    PAUSED = auto()
    RUNNING = auto()
    SHUTTING = auto()

    def __repr__(self) -> str:
        """
        To enable serialization as a string...
        """
        return repr(self.value)


class SimulationRequest(BaseModel):
    """
    JSON describing simulation state.
    rate 0 - pause
    1 - normal rate
    2 - x2 rate, etc
    Returned is SimulationResponse
    """

    state: SimulationState
    rate: float | None = None


class SimulationResponse(BaseModel):
    """
    JSON describing simulation state
    """

    state: SimulationState
    rate: float


class SimultonState(StrEnum):
    """
    Possible values of the Simulton state,
    which is somewhat related to the simulation state
    """

    INIT = auto()
    RUNNING = auto()
    PAUSED = auto()
    SHUTTING = auto()

    def __repr__(self) -> str:
        """
        To enable serialization as a string...
        """
        # default implementation
        # type_ = type(self)
        # module = type_.__module__
        # qualname = type_.__qualname__
        # return f"<{module}.{qualname} object at {hex(id(self))}>"
        return repr(self.value)


class NewSimultonParams(BaseModel):
    """
    JSON describing new simulton
    """

    src_path: str


class SimultonRequest(BaseModel):
    """
    JSON describing simulation state.
    rate 0 - pause
    1 - normal rate
    2 - x2 rate, etc
    Returned is SimulationResponse
    """

    state: SimultonState
    rate: float | None = None


class SimultonResponse(BaseModel):
    """
    JSON describing simulton
    """

    description: str
    port: PositiveInt | None = None
    rate: float
    state: SimultonState
    title: str
    version: str
