"""
Clock Object
"""

import asyncio
import time

# from collections.abc import AsyncGenerator
# from contextlib import asynccontextmanager
# from fastapi import FastAPI, Request
# from fastapi.responses import JSONResponse

# ruff: noqa: I001
from . import (
    #    api_simulton,
    #    api_clocks,
    SimultonState,
    Simulton,
    #    SimultonRequest,
    #    SimultonResponse,
    # NewClockParams,
    ClockResponse,
    # Message,
    # Tags,
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

    def on_paused(self, now: float, rate: float) -> bool:
        """
        Simulation pause event handler
        """
        # log.debug('Clock.on_paused')
        if self._last_start != 0:
            # accumulate _time
            self._time += (now - self._last_start) * rate
            self._last_start = 0
        return True

    def on_running(self, now: float, rate: float) -> bool:
        """
        Simulation run event handler
        """
        # log.debug(f'Clock.on_running({rate})')
        if self._last_start == 0:
            self._last_start = now
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
        return ClockResponse(
            id=self._id, name=self._name, time=self.time, latency=self._latency
        )
