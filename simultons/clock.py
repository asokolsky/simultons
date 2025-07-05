"""
Clock simulation & simulton
"""

# ruff: noqa: I001
import time
from fastapi.responses import JSONResponse

from . import (
    SimultonState,
    Simulton,
    SimultonRequest,
    SimultonResponse,
    NewClockParams,
    ClockResponse,
    Message,
)


class Clock:
    """
    Clock counting simulated time
    """

    def __init__(self, sim: Simulton, name: str) -> None:
        """
        Initializer
        """
        assert sim is not None
        self._sim = sim
        self._id = sim.get_new_instance_id()
        sim.add_instance(self, self._id)
        self._name = name
        # accumulated simulation time until the last pause
        self._time: float = 0
        # os clock
        self._last_start: float = 0
        return

    def on_paused(self) -> bool:
        """
        Simulation pause event handler
        """
        print('Clock.on_paused')
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
        print('Clock.on_running')
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

    def to_response(self) -> ClockResponse:
        return ClockResponse(id=self._id, name=self._name, time=self.time)


class ClockSimulton(Simulton):
    """
    Clock counting simulated time
    """

    title = 'Clock'
    description = 'Clock API'
    version = '0.0.1'

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
        print('ClockSimulton.on_running')
        # notify all the clocks about the change
        for clock in self.instances.values():
            clock.on_running(self._rate)
        return

    def on_paused(self) -> None:
        """
        State just transitioned to PAUSED
        """
        print('ClockSimulton.on_paused')
        # notify all the clocks about the change
        for clock in self.instances.values():
            clock.on_paused()
        return


theClockSimulton: ClockSimulton | None = None  # noqa: N816
app = ClockSimulton.create_app()


@app.on_event('startup')
async def startup_event() -> None:
    print('clock simulton startup_event')
    global theClockSimulton
    theClockSimulton = ClockSimulton()
    theClockSimulton.on_startup()
    return


@app.on_event('shutdown')
async def shutdown_event() -> None:
    global theClockSimulton
    print('clock simulton shutdown_event', theClockSimulton)
    assert theClockSimulton is not None
    theClockSimulton.on_shutdown()
    theClockSimulton = None
    return


@app.get('/api/v1/simulton', response_model=SimultonResponse)
async def get_simulton() -> SimultonResponse:
    print('get clock simulton')
    # global theClockSimulton
    assert theClockSimulton is not None
    return theClockSimulton.to_response()


@app.put('/api/v1/simulton')
async def put_simulton(req: SimultonRequest) -> JSONResponse:
    """
    Handle a request to change the simulton state
    """
    assert theClockSimulton is not None
    return theClockSimulton.on_put_simulton(req)


@app.get('/api/v1/clocks/', response_model=dict[str, ClockResponse])
async def get_instances() -> dict:
    """
    Get all the instances
    """
    if theClockSimulton is None:
        return {}
    return {
        id: cl.to_response().model_dump()
        for id, cl in theClockSimulton.instances.items()
    }


@app.post('/api/v1/clocks/', response_model=ClockResponse, status_code=201)
async def create_instance(params: NewClockParams) -> dict:
    """
    Handle new instance creation
    """
    assert theClockSimulton is not None
    cl = Clock(theClockSimulton, params.name)
    return cl.to_response().model_dump()


@app.get('/api/v1/clocks/{id}', response_model=ClockResponse)
async def get_clock(id: str) -> dict | JSONResponse:
    """
    Get the simulated time
    """
    assert theClockSimulton is not None
    try:
        cl: Clock = theClockSimulton.get_instance_by_id(id)
        return cl.to_response().model_dump()
    except KeyError:
        pass
    content = Message('Item not found').model_dump()
    return JSONResponse(status_code=404, content=content)


@app.delete('/api/v1/clocks/{id}')
async def delete_clock(id: str) -> JSONResponse:
    """
    Delete the clock
    """
    assert theClockSimulton is not None
    try:
        theClockSimulton.del_instance_by_id(id)
        content = Message('OK').model_dump()
        return JSONResponse(status_code=200, content=content)
    except KeyError:
        pass
    content = Message('Item not found').model_dump()
    return JSONResponse(status_code=404, content=content)
