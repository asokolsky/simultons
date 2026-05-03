"""
Test launching/shutting FastAPI server programmatically
"""

import unittest

from simultons import (
    SimultonProxy,
    SimultonState,
    api_elevators,
    api_simulton,
    setup_logging,
)
from simultons.building import NewElevatorParams

log = setup_logging(__name__)


class TestSimulton(unittest.IsolatedAsyncioTestCase):
    """
    Verify launching/shutting a fastapi process
    """

    async def asyncSetUp(self) -> None:
        # log.info('setUp', 'fastapi pid:', self.popen.pid)
        #
        # verify the FastAPI server is running
        #
        self._simulton: SimultonProxy | None = SimultonProxy(
            'simultons/building/elevator.py', 9100
        )
        #
        # start the simulton process
        #
        assert self._simulton.launch()
        assert self._simulton.wait_until_reachable()

        (status_code, _) = self._simulton.restc.get(api_simulton)
        self.assertEqual(status_code, 200)
        return

    async def asyncTearDown(self) -> None:
        log.info('asyncTearDown')
        #
        # shut the simulton process
        #
        if self._simulton is not None:
            await self._simulton.shutdown()
            self._simulton = None
        return

    def test_all(self) -> None:
        """
        Repeat elevator_simulton_test except a real HTTP
        communication is used, not test client.
        """
        # log.info('test_all', 'fastapi pid:', self.popen.pid)
        assert self._simulton is not None
        (status_code, rdata) = self._simulton.restc.get(api_simulton)
        self.assertEqual(status_code, 200)
        self.assertIn(
            rdata['state'], [SimultonState.PAUSED, SimultonState.INIT]
        )
        self.assertEqual(rdata['rate'], 0)
        #
        # Create some elevators
        #
        floors = 10
        names = ['foo', 'bar', 'baz']
        for name in names:
            params = NewElevatorParams(name=name, floors=floors)
            (status_code, rdata) = self._simulton.restc.post(
                api_elevators, params.model_dump()
            )
            self.assertEqual(status_code, 201)
            self.assertEqual(rdata['name'], name)
            self.assertEqual(rdata['floors'], floors)
        #
        # retrieve them all
        #
        (status_code, elevators) = self._simulton.restc.get(api_elevators)
        self.assertEqual(status_code, 200)
        self.assertEqual(len(elevators), len(names))

        for id, el in elevators.items():
            #
            # retrieve them, one at a time
            #
            (status_code, rdata) = self._simulton.restc.get(
                f'{api_elevators}/{id}'
            )
            self.assertEqual(status_code, 200)
            self.assertEqual(rdata, el)
            self.assertIn(el['name'], names)

        return
