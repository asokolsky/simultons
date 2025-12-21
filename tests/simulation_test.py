"""
Testing the simulation stuff
"""

import time
import tracemalloc
import unittest

from simultons import (
    ClockResponse,
    NewClockParams,
    NewSimultonParams,
    SimulationClient,
    SimultonClient,
    SimultonResponse,
    setup_logging,
)

tracemalloc.start()

log = setup_logging(__name__)


class TestSimulation(unittest.TestCase):
    """
    Verify:
      * simulation launcher
      * creation and interaction with simultons
    """

    clock_num = 1

    @classmethod
    def setUpClass(cls) -> None:
        """
        For all the test...
        """
        log.info('TestSimulation.setUpClass')
        return

    @classmethod
    def tearDownClass(cls) -> None:
        """
        After all the tests...
        """
        log.info('TestSimulation.tearDownClass')
        return

    def setUp(self) -> None:
        """
        For every test
        """
        #
        # start the simulation process
        #
        log.info('TestSimulation.setUp')
        self._client = SimulationClient()
        self._client.set_up()
        return

    def tearDown(self) -> None:
        log.info('TestSimulation.tearDown')
        self._client.tear_down()
        return

    def create_clocks(
        self, sc: SimultonClient, num_clocks: int, latency: float
    ) -> dict[str, ClockResponse]:
        """
        Create multiple clocks (in series) in a single singleton.
        Returns dict[clockID, ClockResponse]
        """
        res: dict[str, ClockResponse] = {}
        for _ in range(num_clocks):
            name = f'clock-{self.clock_num}'
            params = NewClockParams(name=name, latency=latency)
            self.clock_num += 1
            (status_code, rdata) = sc.new_collection_item(params.model_dump())
            self.assertEqual(status_code, 201)
            id = rdata['id']
            self.assertTrue(id)
            self.assertEqual(rdata['name'], name)
            time = rdata['time']
            self.assertTrue(str(time))
            res[id] = rdata
        return res

    def create_clock_simultons(
        self, num_simultons: int
    ) -> dict[str, SimultonResponse]:
        res: dict[str, SimultonResponse] = {}
        assert self._client is not None
        param = NewSimultonParams(src_path='simultons/clock.py')
        for _ in range(num_simultons):
            rdata = self._client.post_simulton(param)
            self.assertIsNotNone(rdata)
            # rdata looks like
            # {
            #     'description': '',
            #     'port': 9500,
            #     'rate': 0.0,
            #     'state': 'INIT',
            #     'title': '',
            #     'version': ''
            # }
            assert isinstance(rdata, dict)
            port = rdata['port']
            state = rdata['state']
            self.assertEqual(state, 'PAUSED')
            res[str(port)] = rdata
        return res

    def test_minimal(self) -> None:
        """
        Minimum test of the simulation.
        python3 -m unittest -k test_minimal tests/simulation_test.py
        """
        log.info('test_minimal running')
        assert self._client is not None
        rdata = self._client.get_simulation()
        log.debug(f'get_simulation() => {rdata}')
        self.assertEqual(rdata['state'], 'PAUSED')
        self.assertEqual(rdata['rate'], 0)
        self.assertTrue(rdata['port'])
        #
        # let's run simulation with no simultons now
        #
        rdata = self._client.get_simultons()
        log.info(f'self._client.get_simultons() => {rdata}')
        expected = {}
        self.assertEqual(rdata, expected)
        #
        # lets stop simulation
        #
        return

    def test_one_simulton(self) -> None:
        """
        Test creation of just one clocks simulton.
        python3 -m unittest -k test_one_simulton tests/simulation_test.py
        """
        assert self._client is not None
        rdata = self._client.get_simulation()
        self.assertEqual(rdata['state'], 'PAUSED')
        self.assertEqual(rdata['rate'], 0)
        self.assertTrue(rdata['port'])

        rdata = self._client.get_simultons()
        expected = {}
        self.assertEqual(rdata, expected)

        # create a simulton for a collection of clocks
        param = NewSimultonParams(src_path='simultons/clock.py')
        # note the wait=True here
        rdata = self._client.post_simulton(param)
        self.assertIsInstance(rdata, dict)

        sc = SimultonClient(rdata)
        self.assertEqual(sc._state, 'PAUSED')
        rdata = sc.get_simulton()
        self.assertEqual(sc._state, 'PAUSED')
        clocks = sc.get_collection()
        log.info(f'clocks: {clocks}')
        self.assertEqual(clocks, {})
        #
        # create few fast clocks
        #
        fast_clocks = 5
        fast_latency = 0.1
        clocks_fast = self.create_clocks(sc, fast_clocks, fast_latency)
        log.info(f'clocks_fast: {clocks_fast}')
        #
        # create few fast clocks
        #
        slow_clocks = 5
        slow_latency = 0.3
        clocks_slow = self.create_clocks(sc, slow_clocks, slow_latency)
        log.info(f'clocks_slow: {clocks_slow}')
        #
        # get all clocks
        #
        clocks = sc.get_collection()
        log.info(f'clocks: {clocks}')
        self.assertEqual(len(clocks), len(clocks_fast) + len(clocks_slow))
        self.assertEqual(len(clocks), fast_clocks + slow_clocks)
        #
        # do something, e.g.:
        #   start running simulation
        #   pause simulation
        #   start simulation at x2 rate
        #   pause simulation
        #   verify that the clock time did not change
        #   verify that the clock time did change
        #   verify that the clock time did change
        #   stop simulation
        #   verify that the clock time did not change
        #   verify that the clock time did change
        #   verify that the clock time did not change
        sc.close()
        return

    def test_many_simultons(self) -> None:
        """
        Test N simultons

        To run this test alone:
        python3 -m unittest -k test_many_simultons tests/simulation_test.py
        To watch the simulton processes:
            1. use `ps` or `echo $$` to identify the pid of the shell;
            2. then `watch -c -n 0.1 pstree -p <shell-pid> -Ut`
        """
        N = 15

        assert self._client is not None
        rdata = self._client.get_simulation()
        expected = {'state': 'PAUSED', 'rate': 0}
        self.assertEqual(rdata, expected)

        rdata = self._client.get_simultons()
        expected = {}
        self.assertEqual(rdata, expected)
        #
        # create a few clock simultons
        #
        start = time.time()
        sims = self.create_clock_simultons(N)
        now = time.time()
        log.info(f'Created {N} simultons in {now - start} secs')
        #
        # basic simulton verification
        #
        rdata = self._client.get_simultons()
        assert isinstance(rdata, dict)
        self.assertEqual(len(rdata), len(sims))
        self.assertIsInstance(rdata, dict)
        self.assertEqual(len(rdata), len(sims))
        for id, sim in rdata.items():
            sim0 = sims[id]
            self.assertEqual(sim, sim0)
        #
        # do something, e.g.:
        #   start running simulation
        #   pause simulation
        #   start simulation at x2 rate
        #   pause simulation
        #
        duration = 5
        time.sleep(duration)
        log.info(f'Enjoying {N} simultons for {duration} secs')
        #
        #  verify that the clock time did not change
        #

        return
