"""
Clocks simulton
"""

import asyncio
import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# ruff: noqa: I001
from . import (
    api_simulton,
    api_clocks,
    SimultonState,
    Simulton,
    SimultonRequest,
    SimultonResponse,
    NewClockParams,
    ClockResponse,
    Message,
    Tags,
    setup_logging,
)

log = setup_logging(__name__)


class Clock:
    """
    Clock counting simulated time
    """

    def __init__(self, sim: Simulton, name: str, latency: float) -> None:
        """
        Initializer
        """
        assert sim is not None
        self._sim = sim
        self._id = sim.get_new_instance_id()
        sim.add_instance(self, self._id)
        self._name = name
        self._latency = latency
        # accumulated simulation time until the last pause
        self._time: float = 0
        # os clock
        self._last_start: float = 0
        return

    def on_paused(self) -> bool:
        """
        Simulation pause event handler
        """
        log.debug('Clock.on_paused')
        assert self._sim.is_paused()
        rate = self._sim._rate
        assert rate != 0
        if self._last_start != 0:
            # accumulate _time
            self._time += (time.time() - self._last_start) * rate
            self._last_start = 0
        return True

    def on_running(self, rate: float) -> bool:
        """
        Simulation run event handler
        """
        log.debug('Clock.on_running')
        assert self._sim.is_running()
        assert rate > 0
        if self._last_start == 0:
            self._last_start = time.time()
        return True

    @property
    def time(self) -> float:
        """
        Get the simulation time.
        This can be complex - depends on the simulation state
        """
        if self._sim.state != SimultonState.RUNNING:
            return self._time
        rate = self._sim._rate
        assert rate > 0
        assert self._last_start > 0
        return self._time + ((time.time() - self._last_start) * rate)

    async def to_response(self) -> ClockResponse:
        """
        Return ClockResponse presentation of this clock.
        sleep self._latency seconds to simulate latency.
        """
        if self._latency != 0.0:
            # time.sleep(self._latency)
            await asyncio.sleep(self._latency)
        return ClockResponse(id=self._id, name=self._name, time=self.time)


class ClocksSimulton(Simulton):
    """
    Simulton for a collection of clocks counting simulated time.
    """

    title = 'Clocks'
    summary = 'Clocks API'
    description = 'Clocks API runs at simulation time'
    endpoint = api_clocks

    def __init__(self) -> None:
        """
        Initializer
        """
        super().__init__()
        return

    def on_running(self) -> None:
        """
        State just transitioned to RUNNING
        """
        log.debug('ClocksSimulton.on_running')
        # notify all the clocks about the change
        for clock in self.instances.values():
            clock.on_running(self._rate)
        return

    def on_paused(self) -> None:
        """
        State just transitioned to PAUSED
        """
        log.debug('ClocksSimulton.on_paused')
        # notify all the clocks about the change
        for clock in self.instances.values():
            clock.on_paused()
        return


theClocks: ClocksSimulton | None = None  # noqa: N816


@asynccontextmanager
async def clocks_lifespan(_: FastAPI) -> AsyncGenerator:
    """
    Context manager for managing the application's lifespan events.
    Code before 'yield' runs on startup.
    Code after 'yield' runs on shutdown.
    """
    log.debug('clocks simulton startup_event')
    global theClocks
    theClocks = ClocksSimulton()
    await theClocks.on_startup()

    yield  # The application starts receiving requests after this point

    log.debug(f'clocks simulton shutdown_event {theClocks}')
    await theClocks.on_shutdown()
    theClocks = None
    return


app = ClocksSimulton.create_app(clocks_lifespan)


@app.get(api_simulton, response_model=SimultonResponse, tags=[Tags.simulton])
async def get_simulton(req: Request) -> SimultonResponse:
    log.debug('get clock simulton, port=%d', req.url.port)
    # global theClocks
    assert theClocks is not None
    assert req.url.port is not None
    # no need to await - Simulton.to_response is NOT async
    return theClocks.to_response(req.url.port)


@app.put(api_simulton, tags=[Tags.simulton])
async def put_simulton(req: SimultonRequest, request: Request) -> JSONResponse:
    """
    Handle a request to change the simulton state
    """
    assert theClocks is not None
    assert request.url.port is not None
    return theClocks.on_put_simulton(req, request.url.port)


@app.get(
    api_clocks, response_model=dict[str, ClockResponse], tags=[Tags.clocks]
)
async def get_instances() -> dict:
    """
    Get all the instances
    """
    if theClocks is None:
        return {}
    ids = list(theClocks.instances.keys())
    resps = [cl.to_response() for cl in theClocks.instances.values()]
    # return {
    #    id: (await cl.to_response()).model_dump()
    #    for id, cl in theClocks.instances.items()
    # }
    return {
        id: resp.model_dump()
        for id, resp in zip(ids, await asyncio.gather(*resps), strict=True)
    }


@app.post(
    api_clocks,
    response_model=ClockResponse,
    status_code=201,
    tags=[Tags.clocks],
)
async def create_instance(params: NewClockParams) -> dict:
    """
    Handle new instance creation
    """
    assert theClocks is not None
    cl = Clock(theClocks, params.name, params.latency)
    return (await cl.to_response()).model_dump()


@app.get(api_clocks + '/{id}', response_model=ClockResponse, tags=[Tags.clocks])
async def get_clock(id: str) -> dict | JSONResponse:
    """
    Get the simulated time
    """
    assert theClocks is not None
    try:
        cl: Clock = theClocks.get_instance_by_id(id)
        return (await cl.to_response()).model_dump()
    except KeyError:
        pass
    content = Message('Item not found').model_dump()
    return JSONResponse(status_code=404, content=content)


@app.delete(api_clocks + '/{id}', tags=[Tags.clocks])
async def delete_clock(id: str) -> JSONResponse:
    """
    Delete the clock
    """
    assert theClocks is not None
    try:
        theClocks.del_instance_by_id(id)
        content = Message('OK').model_dump()
        return JSONResponse(status_code=200, content=content)
    except KeyError:
        pass
    content = Message('Item not found').model_dump()
    return JSONResponse(status_code=404, content=content)
