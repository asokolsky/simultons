"""
A simulton is:

* a simulation entity with a REST API
* holds the instances of the relevant class to be accessed via the REST API.

This simulton is not related to https://ogden.eu/simultons/
"""

# ruff: noqa: I001
import asyncio
import json
import os
import random
import signal
import string
import sys
from typing import Any
from starlette.types import Lifespan

import zmq
import zmq.asyncio
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import parse_obj_as
from starlette.background import BackgroundTask

from .globals import make_zspec, simulation_ztopic, module_version
from . import (
    SimulationState,
    SimulationResponse,
    SimultonRequest,
    SimultonResponse,
    SimultonState,
    setup_logging,
)

log = setup_logging(__name__)


def get_random_id() -> str:
    length = 8
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))  # noqa: S311


async def shut_the_process() -> None:
    """
    Call this to exit FastAPI app.
    Sends SIGTERM to the current process
    """
    pid = os.getpid()
    os.kill(pid, signal.SIGTERM)
    log.debug(f'shut_the_process: SIGTERM sent to {pid}')
    return


class Simulton:
    """
    A unit of simulation with REST API exposed via FastAPI(s).
    This class is used as a parent to an actual class to be instantiated in the
    simulton process.
    """

    title = 'FooBar'
    summary = 'FooBar summary'
    description = 'FooBar API'
    endpoint = '/api/v1/foobar'
    version = module_version

    def __init__(self, name: str = '') -> None:
        # reset uvicorn logger
        setup_logging(__name__)
        # from .logging import print_logging_tree
        # print_logging_tree()

        self._port = 0
        self._rate: float = 0
        self._state = SimultonState.INIT
        if not name:
            name = f'{type(self).__qualname__}@{hex(id(self))}'
        self._name = name
        # start zmq subscriber, will be destroyed in on_shutdown
        from .fast_launcher import _ENV_ZSPEC  # noqa: PLC0415

        zspec = os.environ.get(_ENV_ZSPEC) or make_zspec()
        self._zcontext = zmq.asyncio.Context()
        self._zsocket = self._zcontext.socket(zmq.SUB)
        self._zsocket.setsockopt(zmq.SUBSCRIBE, simulation_ztopic.encode())
        self._zsocket.connect(zspec)

        # map of instance ID to the instance itself
        self._instances: dict[str, Any] = {}
        self._bgtasks: set[asyncio.Task] = set()
        return

    async def recv_zmq_string(self) -> str:
        """
        Background async task to receive zmq data
        """
        log.debug('Simulton.recv_zmq_string..')
        try:
            res = await self._zsocket.recv_string()
            log.debug(f'Simulton.recv_zmq_string() => {res}')
            topic, message = res.split()
            assert topic == simulation_ztopic
            # dispatch message
            try:
                self.on_simulation_state_update(
                    parse_obj_as(SimulationResponse, json.loads(message))
                )
            except json.JSONDecodeError as err:
                log.info(f'recv_zmq_string caught JSONDecodeError: {err}')
            except Exception as err:
                log.info(f'recv_zmq_string caught Exception: {err}')
            return message

        except asyncio.exceptions.CancelledError:
            log.debug('Simulton.recv_zmq_string() cancelled')
        return ''

    def on_simulation_state_update(self, resp: SimulationResponse) -> None:
        # compare this to on_put_simulton
        log.debug(f'on_simulation_state_update {resp}')
        if resp.rate is not None:
            self.rate = resp.rate
        if resp.state == SimulationState.PAUSED:
            self.state = SimultonState.PAUSED
        elif resp.state == SimulationState.RUNNING:
            self.state = SimultonState.RUNNING
        elif resp.state == SimulationState.SHUTTING:
            self.state = SimultonState.SHUTTING
            # await shut_the_process()
            pid = os.getpid()
            os.kill(pid, signal.SIGTERM)
            log.debug(f'on_simulation_state_update: SIGTERM sent to {pid}')
        else:
            assert False
        return

    @property
    def state(self) -> SimultonState:
        """Simulton state accessor"""
        return self._state

    @state.setter
    def state(self, state: SimultonState) -> SimultonState:
        """Simulton state setter"""
        if state == self._state:
            return state
        log.debug(f'Simulton {self.title} {self._state} -> {state}')
        # old_state = self._state
        self._state = state
        if state == SimultonState.RUNNING:
            self.on_running()
        elif state == SimultonState.PAUSED:
            self.on_paused()
        elif state == SimultonState.SHUTTING:
            self.on_shutting()
        else:
            assert False
        return state

    def is_running(self) -> bool:
        return self._state == SimultonState.RUNNING

    def is_paused(self) -> bool:
        return self._state == SimultonState.PAUSED

    @property
    def name(self) -> str:
        """
        Name property.
        """
        return self._name

    @property
    def rate(self) -> float:
        """
        Rate property.
        """
        return self._rate

    @rate.setter
    def rate(self, rate: float) -> float:
        """Simulton rate setter"""
        if rate == self._rate:
            return rate
        log.debug(f'Simulton rate {self._rate} -> {rate}')
        self._rate = rate
        return rate

    @property
    def instances(self) -> dict[str, Any]:
        return self._instances

    def on_running(self) -> None:
        """
        State just transitioned to RUNNING
        """
        log.debug('Simulton.on_running')
        return

    def on_paused(self) -> None:
        """
        State just transitioned to PAUSED
        """
        log.debug('Simulton.on_paused')
        return

    def on_shutting(self) -> None:
        """
        State just transitioned to SHUTTING
        """
        log.debug(f'Simulton.on_shutting {self}')
        return

    async def on_startup(self) -> None:
        """
        Simulton FastAPI app startup event handler
        """
        # prepare to read from the zmq socket
        task = asyncio.create_task(self.recv_zmq_string())
        self._bgtasks.add(task)
        # To prevent keeping references to finished tasks forever,
        # make each task remove its own reference from the set after completion
        task.add_done_callback(self._bgtasks.discard)
        self.state = SimultonState.PAUSED
        return

    async def on_shutdown(self) -> None:
        """
        Simulton FastAPI app shutdown event handler
        """
        log.debug(f'on_shutdown {self}')
        # cancel pending zmq recv tasks before closing socket to avoid
        # asyncio exception callbacks from pending recv_string() calls
        for task in list(self._bgtasks):
            task.cancel()
        if self._bgtasks:
            await asyncio.gather(*self._bgtasks, return_exceptions=True)
        # close the zmq subscriber
        # https://zguide.zeromq.org/docs/chapter1/#Making-a-Clean-Exit
        # to avoid hanging infinitely
        try:
            self._zsocket.setsockopt(zmq.LINGER, 0)
            self._zsocket.close()
            self._zcontext.term()
        except Exception as e:
            log.info(f'Caught {type(e)}: {e}')
        # restore stdout/stderr if they were redirected to the parent pipe
        from .fast_launcher import _ENV_REDIRECT_STDOUT  # noqa: PLC0415

        if not os.environ.pop(_ENV_REDIRECT_STDOUT, None):
            return
        sys.stdout.flush()
        sys.stderr.flush()
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        return

    def get_new_instance_id(self) -> str:
        return f'{self.title}-{get_random_id()}'

    def add_instance(self, inst: Any, id: str) -> None:
        assert id
        self._instances[id] = inst
        return

    def get_instance_by_id(self, id: str) -> Any:
        """Raises KeyError if id is not a key"""
        return self._instances[id]

    def del_instance_by_id(self, id: str) -> None:
        """Raises KeyError if id is not a key"""
        del self._instances[id]
        return

    @classmethod
    def create_app(cls, lifespan: Lifespan[FastAPI]) -> FastAPI:
        log.debug(f'Creating a FastAPI app {cls.description}')
        return FastAPI(
            title=cls.title,
            summary=cls.summary,
            description=cls.description,
            version=cls.version,
            lifespan=lifespan,
        )

    def to_response(self, port: int) -> SimultonResponse:
        if self._port == 0:
            self._port = port
        else:
            assert self._port == port
        return SimultonResponse(
            description=self.description,
            endpoint=self.endpoint,
            port=self._port,
            rate=self.rate,
            state=self.state,
            title=self.title,
            version=self.version,
        )

    def on_put_simulton(self, req: SimultonRequest, port: int) -> JSONResponse:
        """
        Handle REST API PUT to change the simulton state
        """
        log.debug(f'on_put_simulton {req} on port {port}')
        if req.rate is not None:
            self.rate = req.rate
        self.state = req.state
        if req.state == SimultonState.SHUTTING:
            background = BackgroundTask(shut_the_process)
        else:
            background = None
        return JSONResponse(
            status_code=202,
            content=self.to_response(port).model_dump(),
            background=background,
        )


#
# the derived class has to have these (see clock.py for an example):
#
# theDerivedSimulton Simulation | None = None # ClockSimulton()
# let's try to delay instantiation to ensure that just importing the package
# does NOT create network resources
#

# @asynccontextmanager
# async def derived_lifespan(_: FastAPI) -> AsyncGenerator:
#     """
#     Context manager for managing the application's lifespan events.
#     Code before 'yield' runs on startup.
#     Code after 'yield' runs on shutdown.
#     """
#     log.debug('derived simulton startup_event')
#     global theDerivedSimulton
#     theDerivedSimulton = DerivedSimulton()
#     await theDerivedSimulton.on_startup()
#
#     yield  # The application starts receiving requests after this point
#
#     assert theDerivedSimulton is not None
#     log.debug(f'simulton shutdown_event {theDerivedSimulton}')
#     await theDerivedSimulton.on_shutdown()
#     theDerivedSimulton = None
#     return

# app = DerivedSimulton.create_app(derived_lifespan)

# @app.get(api_simulton, response_model=SimultonResponse)
# async def get_simulton(req: Request) -> SimultonResponse:
#    '''
#    Get the simulton - state and all
#    '''
#    assert theDerivedSimulton is not None
#    return theDerivedSimulton.to_response(req.url.port)

# @app.put(api_simulton)
# async def put_simulton(params: SimultonRequest, request: Request):
#    '''
#    Handle a request to change the simulton state
#    '''
#    assert theDerivedSimulton is not None
#    return theDerivedSimulton.on_put_simulton(params, request.url.port)
