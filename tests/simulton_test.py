"""
Test launching/shutting FastAPI server programmatically
"""

import unittest

from simultons import NewElevatorParams, SimultonProxy

simulton_uri = '/api/v1/simulton'
elevators_uri = '/api/v1/elevators/'


class TestSimulton(unittest.TestCase):
    """
    Verify launching/shutting a fastapi process
    """

    _service: SimultonProxy | None = None

    @classmethod
    def setUpClass(cls) -> None:
        """
        For all the tests
        """
        print('TestSimulton.setUpClass')
        cls._service = SimultonProxy('simultons/elevator.py', 9000)
        #
        # start the simulton process
        #
        assert cls._service.launch()
        if not cls._service.wait_until_reachable(3):
            cls._service.shutdown()
            assert False
        # save the client
        cls.restc = cls._service._launcher._restc
        return

    @classmethod
    def tearDownClass(cls) -> None:
        """
        Shut FastAPI process
        """
        print('TestSimulton.tearDownClass')
        #
        # shut the simulton process
        #
        cls._service.shutdown()
        return

    def setUp(self) -> None:
        # print('setUp', 'fastapi pid:', self.popen.pid)
        #
        # verify the FastAPI server is running
        #
        (status_code, rdata) = self.restc.get(simulton_uri)
        self.assertEqual(status_code, 200)
        return

    def tearDown(self) -> None:
        # print('tearDown')
        return

    def test_all(self) -> None:
        """
        Repeat elevator_simulton_test except a real HTTP
        communication is used, not test client.
        """
        # print('test_all', 'fastapi pid:', self.popen.pid)

        (status_code, rdata) = self.restc.get(simulton_uri)
        self.assertTrue(status_code, 200)
        self.assertEqual(rdata['state'], 'PAUSED')
        self.assertEqual(rdata['rate'], 0)
        #
        # Create some elevators
        #
        floors = 10
        names = ['foo', 'bar', 'baz']
        for name in names:
            params = NewElevatorParams(name=name, floors=floors)
            (status_code, rdata) = self.restc.post(elevators_uri, params.model_dump())
            self.assertTrue(status_code, 201)
            self.assertTrue(rdata['name'], name)
            self.assertTrue(rdata['floors'], floors)
        #
        # retrieve them all
        #
        (status_code, elevators) = self.restc.get(elevators_uri)
        self.assertTrue(status_code, 200)
        self.assertEqual(len(elevators), len(names))

        for id, el in elevators.items():
            #
            # retrieve them, one at a time
            #
            (status_code, rdata) = self.restc.get(f'{elevators_uri}{id}')
            self.assertTrue(status_code, 200)
            self.assertEqual(rdata, el)
            self.assertIn(el['name'], names)

        return
