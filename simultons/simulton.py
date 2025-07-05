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
from typing import Any

import zmq
import zmq.asyncio
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import parse_obj_as
from starlette.background import BackgroundTask

from .globals import simulation_zspec, simulation_ztopic
from . import (
    SimulationState,
    SimulationResponse,
    SimultonRequest,
    SimultonResponse,
    SimultonState,
)


def get_random_id() -> str:
    length = 8
    return ''.join(random.choice(string.ascii_lowercase) for _ in range(length))  # noqa: S311


async def shut_the_process() -> None:
    """
    Call this to exit FastAPI app
    """
    pid = os.getpid()
    os.kill(pid, signal.SIGTERM)
    print(f'SIGTERM sent to {pid}')
    return


class Simulton:
    """
    A unit of simulation with REST API exposed via FastAPI(s).
    This class is used as a parent to an actual class to be instantiated in the
    simulton process.
    """

    title = 'FooBar'
    description = 'FooBar API'
    version = '0.0.1'

    def __init__(self, name: str = '') -> None:
        self._state = SimultonState.INIT
        self._rate: float = 0
        if not name:
            name = f'{type(self).__qualname__}@{hex(id(self))}'
        self._name = name
        # start zmq subscriber, will be destroyed in on_shutdown
        self._zcontext = zmq.asyncio.Context()
        self._zsocket = self._zcontext.socket(zmq.SUB)
        self._zsocket.setsockopt(zmq.SUBSCRIBE, simulation_ztopic.encode())
        self._zsocket.connect(simulation_zspec)

        # map of instance ID to the instance itself
        self._instances: dict[str, Any] = {}
        self._bgtasks: set[asyncio.Task] = set()
        return

    async def recv_zmq_string(self) -> str:
        """
        Background async task to receive zmq data
        """
        print('Simulton.recv_zmq_string..')
        res = await self._zsocket.recv_string()
        print('Simulton.recv_zmq_string() =>', res)
        topic, message = res.split()
        assert topic == simulation_ztopic
        # dispatch message
        try:
            self.on_simulation_state_update(
                parse_obj_as(SimulationResponse, json.loads(message))
            )
        except json.JSONDecodeError as err:
            print('recv_zmq_string caught JSONDecodeError', err)
        except Exception as err:
            print('recv_zmq_string caught Exception', err)

        return message

    def on_simulation_state_update(self, resp: SimulationResponse) -> None:
        print('on_simulation_state_update', resp)
        if resp.state == SimulationState.PAUSED:
            self.state = SimultonState.PAUSED
        elif resp.state == SimulationState.RUNNING:
            self.state = SimultonState.RUNNING
        elif resp.state == SimulationState.SHUTTING:
            self.state = SimultonState.SHUTTING
            shut_the_process()
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
        print(f'Simulton {self.title} {self._state} -> {state}')
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
        print(f'Simulton rate {self._rate} -> {rate}')
        self._rate = rate
        return rate

    @property
    def instances(self) -> dict[str, Any]:
        return self._instances

    def on_running(self) -> None:
        """
        State just transitioned to RUNNING
        """
        print('Simulton.on_running')
        return

    def on_paused(self) -> None:
        """
        State just transitioned to PAUSED
        """
        print('Simulton.on_paused')
        return

    def on_shutting(self) -> None:
        """
        State just transitioned to SHUTTING
        """
        print('Simulton.on_shutting', self)
        return

    def on_startup(self) -> None:
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

    def on_shutdown(self) -> None:
        """
        Simulton FastAPI app shutdown event handler
        """
        print('Simulton.on_shutdown', self)
        # close the zmq subscriber
        # https://zguide.zeromq.org/docs/chapter1/#Making-a-Clean-Exit
        # to avoid hanging infinitely
        try:
            self._zsocket.setsockopt(zmq.LINGER, 0)
            self._zsocket.close()
            self._zcontext.term()
        except Exception as e:
            print('Caught:', type(e), e)
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
    def create_app(cls) -> FastAPI:
        print('Creating a FastAPI app', cls.description)
        return FastAPI(
            title=cls.title, description=cls.description, version=cls.version
        )

    def to_response(self) -> SimultonResponse:
        return SimultonResponse(
            description=self.description,
            rate=self.rate,
            state=self.state,
            title=self.title,
            version=self.version,
        )

    def on_put_simulton(self, req: SimultonRequest) -> JSONResponse:
        """
        Handle REST API PUT to change the simulton state
        """
        if req.rate is not None:
            self.rate = req.rate
        self.state = req.state
        if req.state == SimultonState.SHUTTING:
            background = BackgroundTask(shut_the_process)
        else:
            background = None
        return JSONResponse(
            status_code=202,
            content=self.to_response().model_dump(),
            background=background,
        )


#
# the derivatives have to have these:
#
# theDerivedSimulton Simulation | None = None # ClockSimulton()
# let's try to delay instantiation to ensure that just importing the package
# does NOT create network resources
#
# app = DerivedSimulton.create_app()

# @app.on_event('startup')
# async def startup_event():
#     global theDerivedSimulton
#     print('simulton startup_event', theDerivedSimulton)
#     theDerivedSimulton = DerivedSimulton()
#     theDerivedSimulton.on_startup()
#     return

# @app.on_event('shutdown')
# async def shutdown_event():
#     global theDerivedSimulton
#     print('simulton shutdown_event', theDerivedSimulton)
#     assert theDerivedSimulton is not None
#     theDerivedSimulton.on_shutdown()
#     theDerivedSimulton = None
#     return

# @app.get('/api/v1/simulton', response_model=SimultonResponse)
# async def get_simulton():
#    '''
#    Get the simulton - state and all
#    '''
#    return theDerivedSimulton.to_response()

# @app.put('/api/v1/simulton')
# async def put_simulton(params: SimultonRequest):
#    '''
#    Handle a request to change the simulton state
#    '''
#    assert theDerivedSimulton.rate is not None
#    return theDerivedSimulton.on_put_simulton(req)
