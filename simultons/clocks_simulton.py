"""
Clocks simulton.
The library does NOT import this file to avoid creating a FastAPI app global.
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
    Clock,
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
        assert self.is_running()
        assert self._rate > 0
        now = time.time()
        # notify all the clocks about the change
        for clock in self.instances.values():
            clock.on_running(now, self._rate)
        return

    def on_paused(self) -> None:
        """
        State just transitioned to PAUSED
        """
        log.debug(f'ClocksSimulton.on_paused {self._state} {self._rate}')

        assert self.is_paused()
        if self._rate == 0:
            # we are paused while in the INIT or PAUSED state
            return
        now = time.time()
        # notify all the clocks about the change
        for clock in self.instances.values():
            clock.on_paused(now, self._rate)
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
