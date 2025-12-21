"""
Test launching/shutting FastAPI server programmatically
"""

import unittest

from simultons import SimultonProxy, api_elevators, api_simulton, setup_logging
from simultons.building import NewElevatorParams

log = setup_logging(__name__)


class TestSimulton(unittest.TestCase):
    """
    Verify launching/shutting a fastapi process
    """

    _simulton: SimultonProxy | None = None

    @classmethod
    def setUpClass(cls) -> None:
        """
        For all the tests
        """
        log.info('TestSimulton.setUpClass')
        cls._simulton = SimultonProxy('simultons/building/elevator.py', 9100)
        #
        # start the simulton process
        #
        assert cls._simulton.launch()
        assert cls._simulton.wait_until_reachable()
        return

    @classmethod
    def tearDownClass(cls) -> None:
        """
        Shut FastAPI process
        """
        log.info('TestSimulton.tearDownClass')
        #
        # shut the simulton process
        #
        assert cls._simulton is not None
        cls._simulton.shutdown()
        return

    def setUp(self) -> None:
        # log.info('setUp', 'fastapi pid:', self.popen.pid)
        #
        # verify the FastAPI server is running
        #
        (status_code, _) = self._simulton.restc.get(api_simulton)
        self.assertEqual(status_code, 200)
        return

    def tearDown(self) -> None:
        # log.info('tearDown')
        return

    def test_all(self) -> None:
        """
        Repeat elevator_simulton_test except a real HTTP
        communication is used, not test client.
        """
        # log.info('test_all', 'fastapi pid:', self.popen.pid)

        (status_code, rdata) = self._simulton.restc.get(api_simulton)
        self.assertTrue(status_code, 200)
        self.assertIn(rdata['state'], ['PAUSED', 'INIT'])
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
            self.assertTrue(status_code, 201)
            self.assertTrue(rdata['name'], name)
            self.assertTrue(rdata['floors'], floors)
        #
        # retrieve them all
        #
        (status_code, elevators) = self._simulton.restc.get(api_elevators)
        self.assertTrue(status_code, 200)
        self.assertEqual(len(elevators), len(names))

        for id, el in elevators.items():
            #
            # retrieve them, one at a time
            #
            (status_code, rdata) = self._simulton.restc.get(
                f'{api_elevators}/{id}'
            )
            self.assertTrue(status_code, 200)
            self.assertEqual(rdata, el)
            self.assertIn(el['name'], names)

        return
