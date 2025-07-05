"""
NewClockParams
All the elevator-related stuff
"""

from enum import auto
from typing import Union

from fastapi.responses import JSONResponse
from fastapi_utils.enums import StrEnum

from . import (
    ButtonWithLedPanel,
    ElevatorResponse,
    Message,
    NewElevatorParams,
    Simulton,
    SimultonRequest,
    SimultonResponse,
)
from .simulton import get_random_id


class LoadValue(StrEnum):
    """
    Possible values of the elevator load
    """

    NONE = auto()
    SOME = auto()
    TOO_MUCH = auto()

    @classmethod
    def is_valid(cls, st: Union[str, 'LoadValue']) -> bool:
        """
        Valid value recognizer
        """
        return st in LoadValue._value2member_map_

    def __repr__(self) -> str:
        """
        To enable serialization as a string...
        """
        return repr(self.value)


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


class Elevator:
    """
    Elevator
    """

    #
    # constant labels
    #
    _label_open_doors = '< >'
    _label_close_doors = '> <'
    #
    # in kg
    #
    _min_load = 1
    _max_load = 700

    def __init__(
        self, sim: Simulton | None, name: str, floors: int, current_floor: int = 0
    ) -> None:
        """
        Initializer
        """
        assert floors > 0
        self._floors = floors
        self._id = ''
        self._name = name
        self._sim = sim
        if sim is None:
            # important for testing
            self._id = get_random_id()
        else:
            self._id = sim.get_new_instance_id()
            sim.add_instance(self, self._id)
        #
        # Instance Attributes
        #
        self._current_floor = current_floor
        self._current_load = 0
        self._destination_floors: list[int] = []
        self._estate = ElevatorState.IDLE
        #
        # Controls - create the control panel
        #
        labels = [str(i) for i in range(1, floors + 1)]
        labels.append(self._label_open_doors)
        labels.append(self._label_close_doors)
        self._panel = ButtonWithLedPanel(labels, self.panel_callback)
        #
        # create indicators here
        # e.g. going up/down, current floor
        #
        return

    def step_in(self, kilos: int) -> bool:
        """
        Passenger of weight kilos steps in
        """
        if kilos <= 0:
            return False
        if self._estate != ElevatorState.DOORS_OPENED:
            return False
        self._current_load += kilos
        return True

    def step_out(self, kilos: int) -> bool:
        """
        Passenger of weight kilos steps out
        """
        if kilos <= 0:
            return False
        if self._estate != ElevatorState.DOORS_OPENED:
            return False
        self._current_load -= kilos
        if self._current_load < 0:  # noqa: PLR1730
            self._current_load = 0
        return True

    @property
    def floors(self) -> int:
        """
        Returns the number of floors
        """
        return self._floors

    @property
    def load(self) -> LoadValue:
        """
        Returns the elevator's load value
        """
        if self._current_load > self._max_load:
            return LoadValue.TOO_MUCH
        if self._current_load > self._min_load:
            return LoadValue.SOME
        return LoadValue.NONE

    def panel_callback(self, panel: ButtonWithLedPanel, leds_on: list[int]) -> None:  # noqa: ARG002
        """
        Handle button press here.
        """
        return

    def __repr__(self) -> str:
        """
        Object print representation
        """
        return (
            f'<{type(self).__qualname__} {self._name} is {self._estate} '
            f'on {self._current_floor} floor {self._panel.annotated_labels} '
            f'at {hex(id(self))}>'
        )

    def floor_call(self, floor: int) -> None:  # noqa: ARG002
        """
        Request for the elevator to go to that floor.
        """
        return

    def to_response(self) -> ElevatorResponse:
        return ElevatorResponse(id=self._id, name=self._name, floors=self._floors)


class ElevatorSimulton(Simulton):
    """
    Simulton for elevators
    """

    title = 'Elevator'
    description = 'Elevator API'
    version = '0.0.1'

    def __init__(self) -> None:
        """
        Initializer
        """
        super().__init__()
        return


theElevatorSimulton: ElevatorSimulton | None = None  # noqa: N816
app = ElevatorSimulton.create_app()


@app.on_event('startup')
async def startup_event() -> None:
    print('elevators startup_event')
    global theElevatorSimulton
    theElevatorSimulton = ElevatorSimulton()
    theElevatorSimulton.on_startup()
    return


@app.on_event('shutdown')
async def shutdown_event() -> None:
    global theElevatorSimulton
    print('elevators shutdown_event', theElevatorSimulton)
    assert theElevatorSimulton is not None
    theElevatorSimulton.on_shutdown()
    theElevatorSimulton = None
    return


@app.get('/api/v1/simulton', response_model=SimultonResponse)
async def get_simulton() -> SimultonResponse:
    print('get elevator simulton')
    # global theElevatorSimulton
    assert theElevatorSimulton is not None
    return theElevatorSimulton.to_response()


@app.put('/api/v1/simulton')
async def put_simulton(req: SimultonRequest) -> JSONResponse:
    """
    Handle a request to change the simulton state
    """
    # global theElevatorSimulton
    assert theElevatorSimulton is not None
    return theElevatorSimulton.on_put_simulton(req)


@app.get('/api/v1/elevators/', response_model=dict[str, ElevatorResponse])
async def get_instances() -> dict:
    """
    Get all the elevators
    """
    # global theElevatorSimulton
    if theElevatorSimulton is None:
        return {}
    return {
        id: el.to_response().model_dump()
        for id, el in theElevatorSimulton.instances.items()
    }


@app.post('/api/v1/elevators/', response_model=ElevatorResponse, status_code=201)
async def create_instance(params: NewElevatorParams) -> dict:
    """
    Handle new instance creation
    """
    assert theElevatorSimulton is not None
    el = Elevator(theElevatorSimulton, params.name, params.floors)
    return el.to_response().model_dump()


@app.get(
    '/api/v1/elevators/{id}',
    response_model=ElevatorResponse,
    responses={404: {'model': Message}},
)
async def get_elevator(id: str) -> JSONResponse:
    """
    Get the specific elevator
    """
    # global theElevatorSimulton
    assert theElevatorSimulton is not None
    try:
        el = theElevatorSimulton.get_instance_by_id(id)
        return JSONResponse(status_code=200, content=el.to_response().model_dump())
    except KeyError:
        pass
    content = Message('Item not found').model_dump()
    return JSONResponse(status_code=404, content=content)


@app.delete('/api/v1/elevators/{id}')
async def delete_elevator(id: str) -> JSONResponse:
    """
    Delete the elevator
    """
    assert theElevatorSimulton is not None
    try:
        theElevatorSimulton.del_instance_by_id(id)
        return JSONResponse(status_code=200, content={})
    except KeyError:
        pass
    content = Message('Item not found').model_dump()
    return JSONResponse(status_code=404, content=content)
