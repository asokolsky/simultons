"""
Testing the simulation stuff
"""

import asyncio
import time
import tracemalloc
import unittest
from typing import Any

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


class TestSimulation(unittest.IsolatedAsyncioTestCase):
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

    async def asyncSetUp(self) -> None:
        """
        For every test
        """
        #
        # start the simulation process
        #
        log.info('asyncSetUp')
        self._client = SimulationClient()
        self._client.set_up()

        self._simulton_client: SimultonClient | None = None
        return

    async def asyncTearDown(self) -> None:
        log.info('asyncTearDown')
        if self._simulton_client is not None:
            await self._simulton_client.close()
            self._simulton_client = None
        await self._client.tear_down()
        return

    def create_clocks_simulton(self) -> SimultonClient:
        """
        Create a new simulton for a collection of clocks
        """
        param = NewSimultonParams(src_path='simultons/clock.py')
        # note the wait=True here
        assert self._client is not None
        res = self._client.post_simulton(param)
        assert res is not None
        simulton_client = SimultonClient(res)
        self.assertEqual(simulton_client._state, 'PAUSED')
        return simulton_client

    def create_clocks_simultons(
        self, num_simultons: int
    ) -> dict[str, SimultonResponse]:
        res: dict[str, SimultonResponse] = {}
        assert self._client is not None
        param = NewSimultonParams(src_path='simultons/clock.py')
        for _ in range(num_simultons):
            r = self._client.post_simulton(param)
            self.assertIsNotNone(r)
            # r looks like
            # {
            #     'description': '',
            #     'port': 9500,
            #     'rate': 0.0,
            #     'state': 'INIT',
            #     'title': '',
            #     'version': ''
            # }
            assert isinstance(r, SimultonResponse)
            self.assertEqual(r.state, 'PAUSED')
            res[str(r.port)] = r
        return res

    async def create_clocks(
        self, sc: SimultonClient, num_clocks: int, latency: float
    ) -> dict[str, ClockResponse]:
        """
        Create multiple clocks (in series) in a single singleton.
        Returns dict[clockID, ClockResponse]
        """
        tasks = [
            sc.async_new_collection_item(
                NewClockParams(
                    name=f'clock-{clock_num}', latency=latency
                ).model_dump()
            )
            for clock_num in range(self.clock_num, self.clock_num + num_clocks)
        ]
        self.clock_num += num_clocks

        start = time.time()
        resp = await asyncio.gather(*tasks)
        dt = time.time() - start
        log.info(
            f'Created {num_clocks} clocks with latency {latency} in {dt} secs'
        )
        self.assertGreater(dt, latency)

        res: dict[str, ClockResponse] = {}
        for status_code, rdata in resp:
            self.assertEqual(status_code, 201)
            self.assertTrue(rdata['id'])
            self.assertTrue(rdata['name'])
            self.assertTrue(str(rdata['time']))
            res[rdata['id']] = rdata
        return res

    def get_time(
        self, simulton_client: SimultonClient, clock_id: str, latency: float
    ) -> dict:
        """
        Retrieve the time from a specific clock and verify its latency
        """
        assert simulton_client is not None
        start = time.time()
        rdata = simulton_client.get_collection_item(clock_id)
        dt = time.time() - start
        assert rdata is not None
        self.assertGreater(dt, latency)
        return rdata

    def test_minimal(self) -> None:
        """
        Minimum test of the simulation.
        python3 -m unittest -k test_minimal tests/simulation_test.py
        """
        log.info('test_minimal running')
        assert self._client is not None
        sim = self._client.get_simulation()
        log.debug(f'get_simulation() => {sim}')
        assert sim is not None
        self.assertEqual(sim.state, 'PAUSED')
        self.assertEqual(sim.rate, 0)
        self.assertTrue(sim.port)
        #
        # we are running simulation with no simultons!
        #
        rdata = self._client.get_simultons()
        log.info(f'self._client.get_simultons() => {rdata}')
        expected: dict = {}
        self.assertEqual(rdata, expected)
        return

    def test_minimal_one_simulton(self) -> None:
        """
        Minimum test of the simulation + 1 simulton.
        python3 -m unittest -k test_minimal_one_simulton tests/simulation_test.py
        """
        log.info('test_minimal_one_simulton running')
        self._simulton_client = self.create_clocks_simulton()
        clocks = self._simulton_client.get_collection()
        log.info(f'clocks: {clocks}')
        self.assertEqual(clocks, {})

        nonexistent_id = '1234567890'
        self.assertIsNone(
            self._simulton_client.get_collection_item(nonexistent_id)
        )
        self.assertIsNone(
            self._simulton_client.del_collection_item(nonexistent_id)
        )
        return

    async def test_one_simulton(self) -> None:
        """
        Test creation of just one clocks simulton.
        python3 -m unittest -k test_one_simulton tests/simulation_test.py
        """
        log.info('test_one_simulton running')

        assert self._client is not None
        sim = self._client.get_simulation()
        assert sim is not None
        self.assertEqual(sim.state, 'PAUSED')
        self.assertEqual(sim.rate, 0)
        self.assertTrue(sim.port)

        simultons = self._client.get_simultons()
        expected: dict = {}
        self.assertEqual(simultons, expected)

        # create a simulton for a collection of clocks
        # note the wait=True here
        res = self._client.post_simulton(
            NewSimultonParams(src_path='simultons/clock.py')
        )
        assert res is not None
        self._simulton_client = SimultonClient(res)
        self.assertEqual(self._simulton_client._state, 'PAUSED')
        res = self._simulton_client.get_simulton()
        self.assertEqual(self._simulton_client._state, 'PAUSED')
        clocks = self._simulton_client.get_collection()
        log.info(f'clocks: {clocks}')
        self.assertEqual(clocks, {})
        # ID of the clock that does not exist
        nonexistent_id = '1234567890'
        #
        # verify nonexistent clock access
        #
        self.assertIsNone(
            self._simulton_client.get_collection_item(nonexistent_id)
        )
        self.assertIsNone(
            self._simulton_client.del_collection_item(nonexistent_id)
        )
        #
        # create few fast clocks
        #
        num_fast_clocks = 4
        fast_latency = 0.1
        fast_clocks = await self.create_clocks(
            self._simulton_client, num_fast_clocks, fast_latency
        )
        log.info(f'clocks_fast: {fast_clocks}')
        self.assertEqual(len(fast_clocks), num_fast_clocks)
        #
        # create few slow clocks
        #
        num_slow_clocks = 5
        slow_latency = 0.3
        slow_clocks = await self.create_clocks(
            self._simulton_client, num_slow_clocks, slow_latency
        )
        log.info(f'clocks_slow: {slow_clocks}')
        self.assertEqual(len(slow_clocks), num_slow_clocks)
        #
        # get all clocks
        #
        clocks = self._simulton_client.get_collection()
        log.info(f'clocks: {clocks}')
        self.assertEqual(len(clocks), len(fast_clocks) + len(slow_clocks))
        self.assertEqual(len(clocks), num_fast_clocks + num_slow_clocks)
        #
        # verify nonexistent clock access
        #
        self.assertIsNone(
            self._simulton_client.get_collection_item(nonexistent_id)
        )
        self.assertIsNone(
            self._simulton_client.del_collection_item(nonexistent_id)
        )
        #
        # retrieve the clock values
        #
        theFastClockId = next(iter(fast_clocks.keys()))
        rdata = self.get_time(
            self._simulton_client, theFastClockId, fast_latency
        )
        self.assertEqual(rdata, clocks[theFastClockId])
        self.assertEqual(rdata['time'], 0.0)

        theSlowClockId = next(iter(slow_clocks.keys()))
        rdata = self.get_time(
            self._simulton_client, theSlowClockId, slow_latency
        )
        self.assertEqual(rdata, clocks[theSlowClockId])
        self.assertEqual(rdata['time'], 0.0)

        # pause it
        assert self._client is not None
        self.assertTrue(self._client.pause())
        # start it at normal rate
        self.assertTrue(self._client.run())

        # sleep for a pre-defined period
        duration = 0.2
        await asyncio.sleep(duration)

        # retrieve the theClockId clock
        rdata = self.get_time(
            self._simulton_client, theFastClockId, fast_latency
        )
        assert isinstance(rdata, dict)
        self.assertGreater(rdata['time'], duration + fast_latency)
        log.info(f'I slept for {duration} clock {rdata["time"]}')

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
        assert isinstance(rdata, dict)
        self.assertEqual(rdata['state'], 'PAUSED')
        self.assertEqual(rdata['rate'], 0)
        self.assertTrue(rdata['port'])

        rdata = self._client.get_simultons()
        expected: dict[str, Any] = {}
        self.assertEqual(rdata, expected)
        #
        # create a few clock simultons
        #
        start = time.time()
        sims = self.create_clocks_simultons(N)
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
