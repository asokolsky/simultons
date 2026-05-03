"""
Some of the elevator-related stuff
"""

import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from enum import auto
from typing import Union

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi_utils.enums import StrEnum

from simultons import (
    Clock,
    Message,
    Simulton,
    SimultonRequest,
    SimultonResponse,
    Tags,
    api_elevators,
    api_simulton,
    # get_random_id,
    setup_logging,
)

from . import (
    ButtonWithLedPanel,
    ElevatorResponse,
    ElevatorState,
    NewElevatorParams,
)

log = setup_logging(__name__)


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


class Elevator(Clock):
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
        self,
        sim: Simulton,
        name: str,
        floors: int,
        current_floor: int = 0,
    ) -> None:
        """
        Initializer
        """
        super().__init__(sim, name, 0.0)
        #
        # Instance Attributes
        #
        assert floors > 0
        self._floors = floors
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

    def panel_callback(
        self, panel: ButtonWithLedPanel, leds_on: list[int]
    ) -> None:
        """
        Handle button press here.
        """
        log.debug(f'panel_callback {panel} {leds_on}')
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

    async def to_response(self) -> ElevatorResponse:
        return ElevatorResponse(
            id=self._id,
            name=self._name,
            time=self._time,
            latency=self._latency,
            state=self._estate,
            current_floor=self._current_floor,
            floors=self._floors,
        )


class ElevatorsSimulton(Simulton):
    """
    Simulton for elevators
    """

    title = 'Elevator'
    summary = 'Elevator API'
    description = 'Elevator simulton can do so many things....'

    def __init__(self) -> None:
        """
        Initializer
        """
        super().__init__()
        return


@asynccontextmanager
async def elevators_lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Context manager for managing the application's lifespan events.
    Code before 'yield' runs on startup.
    Code after 'yield' runs on shutdown.
    """
    log.debug('elevators startup_event')
    app.state.simulton = ElevatorsSimulton()
    await app.state.simulton.on_startup()

    yield  # The application starts receiving requests after this point

    log.debug(f'elevators shutdown_event {app.state.simulton}')
    await app.state.simulton.on_shutdown()
    return


app = ElevatorsSimulton.create_app(elevators_lifespan)


@app.get(api_simulton, response_model=SimultonResponse, tags=[Tags.simulton])
async def get_simulton(req: Request) -> SimultonResponse:
    log.debug('get elevator simulton')
    assert req.url.port is not None
    simulton: ElevatorsSimulton = req.app.state.simulton
    return simulton.to_response(req.url.port)


@app.put(api_simulton, tags=[Tags.simulton])
async def put_simulton(req: SimultonRequest, request: Request) -> JSONResponse:
    """
    Handle a request to change the simulton state
    """
    assert request.url.port is not None
    simulton: ElevatorsSimulton = request.app.state.simulton
    return simulton.on_put_simulton(req, request.url.port)


@app.get(
    api_elevators,
    response_model=dict[str, ElevatorResponse],
    tags=[Tags.elevators],
)
async def get_instances(request: Request) -> dict:
    """
    Get all the elevators
    """
    simulton: ElevatorsSimulton = request.app.state.simulton
    ids = list(simulton.instances.keys())
    resps = [el.to_response() for el in simulton.instances.values()]
    return {
        id: resp.model_dump()
        for id, resp in zip(ids, await asyncio.gather(*resps), strict=True)
    }


@app.post(
    api_elevators,
    response_model=ElevatorResponse,
    status_code=201,
    tags=[Tags.elevators],
)
async def create_instance(params: NewElevatorParams, request: Request) -> dict:
    """
    Handle new instance creation
    """
    el = Elevator(request.app.state.simulton, params.name, params.floors)
    return (await el.to_response()).model_dump()


@app.get(
    api_elevators + '/{id}',
    response_model=ElevatorResponse,
    responses={404: {'model': Message}},
    tags=[Tags.elevators],
)
async def get_elevator(id: str, request: Request) -> JSONResponse:
    """
    Get the specific elevator
    """
    try:
        simulton: ElevatorsSimulton = request.app.state.simulton
        el = simulton.get_instance_by_id(id)
        return JSONResponse(
            status_code=200, content=(await el.to_response()).model_dump()
        )
    except KeyError:
        pass
    content = Message('Item not found').model_dump()
    return JSONResponse(status_code=404, content=content)


@app.delete(api_elevators + '/{id}', tags=[Tags.elevators])
async def delete_elevator(id: str, request: Request) -> JSONResponse:
    """
    Delete the elevator
    """
    try:
        request.app.state.simulton.del_instance_by_id(id)
        return JSONResponse(status_code=200, content={})
    except KeyError:
        pass
    content = Message('Item not found').model_dump()
    return JSONResponse(status_code=404, content=content)
