"""
Simulation launches all the simultons
"""

import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.background import BackgroundTask
import zmq
import zmq.asyncio

# ruff: noqa: I001
from .globals import simulation_zspec, simulation_ztopic, module_version

from . import (
    api_simulation,
    api_simultons,
    SimulationState,
    SimulationRequest,
    SimulationResponse,
    NewSimultonParams,
    SimultonProxy,
    SimultonResponse,
    Tags,
    Message,
    load_yaml,
    setup_logging,
    shut_the_process,
)

log = setup_logging(__name__)


class Simulation:
    """
    Simulation launcher
    """

    _zspec = simulation_zspec
    _ztopic = simulation_ztopic

    def __init__(self) -> None:
        """
        Initializer
        """
        # reset uvicorn logger
        global log
        log = setup_logging(__name__)
        # init members
        self._port = 1
        self._state = SimulationState.INIT
        # start in paused
        self._rate = 0.0
        # start zmq publisher - destroyed in on_shutdown
        self._zcontext = zmq.asyncio.Context()
        self._zsocket = self._zcontext.socket(zmq.PUB)
        self._zsocket.bind(self._zspec)
        # simulton accumulator
        # NOTE: do NOT use _simultons to iterate and communicate with simultons
        # instead use _zsocket to broadcast the update to all the simultons
        self._simultons: dict[int, SimultonProxy] = {}
        settings = load_yaml('settings.yaml')
        log.debug(f'settings: {settings}')
        assert isinstance(settings, dict)
        sim_settings = settings['simulation']
        assert isinstance(sim_settings, dict)
        self._next_simulton_port = sim_settings['first_simulton_port']
        return

    def to_response(self, port: int | None = None) -> SimulationResponse:
        if port is None:
            pass
        elif self._port == 1:
            self._port = port
        else:
            assert self._port == port
        return SimulationResponse(
            state=self._state, rate=self._rate, port=self._port
        )

    async def broadcast_state_update(self) -> None:
        """
        Share the state update with all the subscribers.
        """
        message = self.to_response().model_dump_json()
        assert self._zsocket is not None
        log.debug(f'Broadcasting state update: {message}')
        self._zsocket.send_string(f'{self._ztopic} {message}')
        return

    @property
    def state(self) -> SimulationState:
        """Simulation state"""
        return self._state

    async def setState(self, state: SimulationState) -> SimulationState:  # noqa: N802
        if self._state == state:
            return state
        log.debug(f'state {self._state} -> {state}')
        # update the state first
        self._state = state
        await self.broadcast_state_update()
        # self.broadcast_state_update()
        return state

    @property
    def rate(self) -> float:
        """Simulation rate, 0 for paused"""
        return self._rate

    @rate.setter
    def rate(self, rate: float) -> float:
        if self._rate == rate:
            return rate
        log.debug(f'Simulation rate {self._rate} -> {rate}')
        self._rate = rate
        return self._rate

    def is_paused(self) -> bool:
        """
        Check it is it paused.
        """
        return self._state == SimulationState.PAUSED

    def __repr__(self) -> str:
        """
        Object print representation
        """
        return (
            f'<{type(self).__qualname__} is {self._state}'
            f' at {self._rate} at {hex(id(self))}>'
        )

    async def on_startup(self) -> None:
        """
        Simulation FastAPI startup event handler
        """
        log.debug('on_startup')
        await self.setState(SimulationState.PAUSED)
        return

    async def on_shutdown(self) -> None:
        """
        Simulation FastAPI shutdown event handler
        """
        log.debug(f'on_shutdown {self}')
        await asyncio.gather(
            *[s.close_sockets() for s in self._simultons.values()]
        )

        await self.setState(SimulationState.SHUTTING)
        log.debug('Closing zmq publisher')
        #
        # close the zmq publisher to avoid hanging infinitely
        #
        self._zsocket.setsockopt(zmq.LINGER, 0)
        self._zsocket.close()
        self._zcontext.term()
        log.debug('Shutting the simulton proxies')
        await asyncio.gather(*[s.shutdown() for s in self._simultons.values()])
        return

    async def create_simulton(
        self, params: NewSimultonParams
    ) -> SimultonResponse:
        """
        Handle new simulton creation
        """
        simulton = SimultonProxy(params.src_path, self._next_simulton_port)
        if not simulton.launch():
            raise ValueError(f'Bad path {params.src_path}')
        self._simultons[simulton.port] = simulton
        self._next_simulton_port += 1
        # wait to hear from it...
        await simulton.async_wait_until_reachable()
        return simulton.to_simulton_response()


@asynccontextmanager
async def simulation_lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Context manager for managing the application's lifespan events.
    Code before 'yield' runs on startup.
    Code after 'yield' runs on shutdown.
    """
    log.debug('simulation startup_event')
    app.state.simulation = Simulation()
    await app.state.simulation.on_startup()

    yield  # The application starts receiving requests after this point

    log.debug('simulation shutdown_event')
    await app.state.simulation.on_shutdown()
    return


"""
Create a REST API service
"""
app = FastAPI(
    title='Simulation',
    summary='Simulation with Simultons.',
    description="""
Simulation runs multiple Simultons, each of them in their own process and with their own REST API endpoint.

## Simulation Endpoint

Can be used to manipulate the state of the simulation

## Simultons Endpoint

Can be used to create new simultons, destroy them, etc.
""",
    version=module_version,
    lifespan=simulation_lifespan,
)


@app.get(api_simulation, tags=[Tags.simulation])
async def get_simulation(req: Request) -> SimulationResponse:
    """
    Get the simulation state
    """
    simulation: Simulation = req.app.state.simulation
    return simulation.to_response(req.url.port)


@app.put(
    api_simulation,
    response_model=SimulationResponse,
    status_code=202,
    responses={400: {'model': Message}},
    tags=[Tags.simulation],
)
async def put_simulation(
    req: SimulationRequest, request: Request
) -> JSONResponse:
    """
    Update the simulation state
    """
    log.debug(f'put_simulation({req})')
    simulation = request.app.state.simulation
    if req.rate is not None:
        simulation.rate = req.rate
    await simulation.setState(req.state)
    if simulation.state == SimulationState.SHUTTING:
        background = BackgroundTask(shut_the_process)
    else:
        background = None
    content = simulation.to_response().model_dump()
    return JSONResponse(status_code=202, content=content, background=background)


@app.post(
    api_simultons,
    response_model=SimultonResponse,
    status_code=201,
    responses={400: {'model': Message}},
    tags=[Tags.simultons],
)
async def create_simulton(
    params: NewSimultonParams,
    request: Request,
) -> SimultonResponse | JSONResponse:
    """
    Handle new simulton creation
    """
    simulation: Simulation = request.app.state.simulation
    try:
        return await simulation.create_simulton(params)
    except ValueError as err:
        content = Message(f'Bummer: {err}').model_dump()
        return JSONResponse(status_code=400, content=content)


@app.get(
    api_simultons,
    response_model=dict[int, SimultonResponse],
    tags=[Tags.simultons],
)
async def get_simultons(request: Request) -> dict:
    """
    Get all the simultons
    """
    # NOTE: this does NOT involve talking to simultons
    return {
        port: s.to_simulton_response()
        for port, s in request.app.state.simulation._simultons.items()
    }


@app.get(
    api_simultons + '/{id}',
    response_model=SimultonResponse,
    responses={404: {'model': Message}},
    tags=[Tags.simultons],
)
async def get_simulton(
    id: int, request: Request
) -> SimultonResponse | JSONResponse:
    """
    Get the simulation
    """
    simulation: Simulation = request.app.state.simulation
    try:
        return simulation._simultons[id].to_simulton_response()
    except IndexError:
        pass
    content = Message('Item not found').model_dump()
    return JSONResponse(status_code=404, content=content)
