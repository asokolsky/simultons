"""
Testing the simulation stuff
"""

import time
import unittest

import httpx

from simultons import (
    FastLauncher,
    NewSimultonParams,
    SimulationRequest,
    SimulationState,
    SimultonResponse,
    wait_until_reachable,
)

simulation_uri = '/api/v1/simulation'
simultons_uri = '/api/v1/simultons'


class TestSimulation(unittest.TestCase):
    """
    Verify:
      * simulation launcher
      * creation and interaction with simultons
    """

    @classmethod
    def setUpClass(cls) -> None:
        """
        For all the test...
        """
        print('TestSimulation.setUpClass')
        return

    @classmethod
    def tearDownClass(cls) -> None:
        """
        After all the tests...
        """
        print('TestSimulation.tearDownClass')
        return

    def setUp(self) -> None:
        """
        For every test
        """
        print('TestSimulation.setUp')
        self._service = FastLauncher('simultons/simulation.py', 9000)
        #
        # start the simulation process
        #
        assert self._service.launch()
        res = self._service.wait_until_reachable(simulation_uri, 3)
        if not res:
            self._service.shutdown()
            assert False
        expected = {'state': 'PAUSED', 'rate': 0.0}
        self.assertEqual(res, expected)
        #
        #
        # create simulation REST client
        #
        verbose = True
        dumpHeaders = False
        self.restc = self._service.get_rest_client(verbose, dumpHeaders)
        return

    def tearDown(self) -> None:
        print('TestSimulation.tearDown')
        # request simulation process shutdown
        try:
            req = SimulationRequest(state=SimulationState.SHUTTING)
            (status_code, rdata) = self.restc.put(simulation_uri, req.model_dump())
            self._service.wait_to_die(5)
        except httpx.ReadTimeout as err:
            print('Caught in TestSimulation.tearDown:', err)
            # pass

        time.sleep(0.1)
        self._service.shutdown(timeout=3)
        self._service = None

        # self.restc.close()
        self.restc = None
        return

    def test_minimal(self) -> None:
        """
        Minimum test of the simulation API
        python3 -m unittest -k test_minimal tests/simulation_test.py
        """
        assert self.restc is not None
        (status_code, rdata) = self.restc.get(simulation_uri)
        self.assertTrue(status_code, 200)
        expected = {'state': 'PAUSED', 'rate': 0}
        self.assertEqual(rdata, expected)
        return

    def create_clock_simultons(self, num_simultons: int) -> dict[str, SimultonResponse]:
        res: dict[str, SimultonResponse] = {}
        assert self.restc is not None
        for _ in range(num_simultons):
            params = NewSimultonParams(src_path='simultons/clock.py')
            (status_code, rdata) = self.restc.post(simultons_uri, params.model_dump())
            self.assertEqual(status_code, 201)
            # rdata looks like
            # {
            #     'description': '',
            #     'port': 9500,
            #     'rate': 0.0,
            #     'state': 'INIT',
            #     'title': '',
            #     'version': ''
            # }
            port = rdata['port']
            state = rdata['state']
            self.assertEqual(state, 'INIT')
            res[str(port)] = rdata
        return res

    def test_one_simulton(self) -> None:
        """
        Minimum test of the simulation API
        """
        assert self.restc is not None
        (status_code, rdata) = self.restc.get(simulation_uri)
        self.assertTrue(status_code, 200)
        expected = {'state': 'PAUSED', 'rate': 0}
        self.assertEqual(rdata, expected)
        (status_code, rdata) = self.restc.get(simultons_uri)
        self.assertTrue(status_code, 200)
        expected = {}
        self.assertEqual(rdata, expected)

        sims = self.create_clock_simultons(1)
        print(sims)
        self.assertEqual(len(sims), 1)
        for port in sims:
            # reach out to the sim!
            url = f'http://127.0.0.1:{port}/api/v1/clocks/'
            res = wait_until_reachable(url, 5)
            self.assertTrue(res)
            print('Clocks:', res)
        return

    def test_many_simultons(self) -> None:
        """
        Test N simultons

        To run this test alone:
        python3 -m unittest -k test_many_simultons tests/simulation_test.py
        To watch the simulton processes:
            1. use `ps` to identify the pid of the shell;
            2. then
            watch -c -n 0.1  pstree -p <shell-pid> -Ut
        """
        assert self.restc is not None
        (status_code, rdata) = self.restc.get(simulation_uri)
        self.assertTrue(status_code, 200)
        expected = {'state': 'PAUSED', 'rate': 0}
        self.assertEqual(rdata, expected)

        (status_code, rdata) = self.restc.get(simultons_uri)
        self.assertTrue(status_code, 200)
        expected = {}
        self.assertEqual(rdata, expected)
        #
        # create a few clock simultons
        #
        start = time.time()
        N = 15
        sims = self.create_clock_simultons(N)
        now = time.time()
        print(f'Created {N} simultons in {now - start} secs')

        (status_code, rdata) = self.restc.get(simultons_uri)
        self.assertTrue(status_code, 200)
        self.assertEqual(len(rdata), len(sims))
        self.assertIsInstance(rdata, dict)

        self.assertEqual(len(rdata), len(sims))
        for id, sim in rdata.items():
            sim0 = sims[id]
            self.assertEqual(sim, sim0)

        duration = 5
        time.sleep(duration)
        print(f'Enjoying {N} simultons for {duration} secs')

        return
