"""
Testing the simulation stuff
"""

import time
import unittest

from simultons import (
    NewSimultonParams,
    SimulationClient,
    SimultonResponse,
    api_simulton,
    setup_logging,
    wait_until_reachable,
)

log = setup_logging(__name__)


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

    def test_minimal(self) -> None:
        """
        Minimum test of the simulation API
        python3 -m unittest -k test_minimal tests/simulation_test.py
        """
        assert self._client is not None
        rdata = self._client.get_simulation()
        expected = {'state': 'PAUSED', 'rate': 0}
        self.assertEqual(rdata, expected)
        #
        # let's run simulation with no simultons now
        #
        log.info('test_minimal running')
        rdata = self._client.get_simultons()
        log.info(f'self._client.get_simultons() => {rdata}')
        expected = {}
        self.assertEqual(rdata, expected)
        #
        # lets stop simulation
        #
        return

    def create_clock_simultons(self, num_simultons: int) -> dict[str, SimultonResponse]:
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

    def test_one_simulton(self) -> None:
        """
        Test creation of just one simulton.
        python3 -m unittest -k test_one_simulton tests/simulation_test.py
        """
        assert self._client is not None
        rdata = self._client.get_simulation()
        expected = {'state': 'PAUSED', 'rate': 0}
        self.assertEqual(rdata, expected)

        rdata = self._client.get_simultons()
        expected = {}
        self.assertEqual(rdata, expected)

        sims = self.create_clock_simultons(1)
        log.debug(sims)
        self.assertEqual(len(sims), 1)
        for port in sims:
            # reach out to the sim!
            url = f'http://127.0.0.1:{port}{api_simulton}'
            res = wait_until_reachable(url)
            log.debug(f'simulton: {res}')
            self.assertIsNotNone(res)
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
