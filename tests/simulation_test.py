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
    SimulationResponse,
    SimultonClient,
    SimultonResponse,
    load_yaml,
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
        param = NewSimultonParams(src_path='simultons/clocks_simulton.py')
        assert self._client is not None
        res = self._client.post_simulton(param)
        assert res is not None
        simulton_client = SimultonClient(res)
        self.assertEqual(simulton_client._state, 'PAUSED')
        return simulton_client

    async def create_clocks_simultons(
        self, num_simultons: int
    ) -> dict[int, SimultonResponse]:
        """
        Create N simultons (in parallel)
        """
        assert self._client is not None
        param = NewSimultonParams(src_path='simultons/clocks_simulton.py')
        tasks = [
            self._client.async_post_simulton(param)
            for _ in range(num_simultons)
        ]
        start = time.time()
        resps = await asyncio.gather(*tasks)
        dt = time.time() - start
        log.info(f'Created {num_simultons} simultons in {dt:.2f} secs')

        res: dict[int, SimultonResponse] = {}
        for resp in resps:
            assert isinstance(resp, SimultonResponse)
            self.assertEqual(resp.state, 'PAUSED')
            assert isinstance(resp.port, int)
            self.assertIsInstance(resp.port, int)
            res[resp.port] = resp
        return res

    async def create_clocks(
        self, sc: SimultonClient, num_clocks: int, latency: float
    ) -> dict[str, ClockResponse]:
        """
        Create multiple clocks (in parallel) in a single singleton.
        Returns dict[clockID, ClockResponse]
        """
        tasks = [
            sc.new_item(
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
            f'Created {num_clocks} clocks with latency {latency} in {dt:.2f} secs'
        )
        self.assertGreater(dt, latency)

        res: dict[str, ClockResponse] = {}
        for rdata in resp:
            assert isinstance(rdata, dict)
            self.assertTrue(rdata['id'])
            self.assertTrue(rdata['name'])
            self.assertTrue(str(rdata['time']))
            res[rdata['id']] = ClockResponse(**rdata)
        return res

    async def get_time(
        self, simulton_client: SimultonClient, clock_id: str, latency: float
    ) -> dict:
        """
        Retrieve the time from a specific clock and verify its latency
        """
        assert simulton_client is not None
        start = time.time()
        rdata = await simulton_client.get_item(clock_id)
        dt = time.time() - start
        assert rdata is not None
        self.assertGreater(dt, latency)
        return rdata

    async def test_minimorum(self) -> None:
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

    async def test_minimal_one_simulton(self) -> None:
        """
        Minimum test of the simulation + 1 simulton.
        python3 -m unittest -k test_minimal_one_simulton tests/simulation_test.py
        """
        log.info('test_minimal_one_simulton running')
        self._simulton_client = self.create_clocks_simulton()
        clocks = await self._simulton_client.get_items()
        log.info(f'clocks: {clocks}')
        self.assertEqual(clocks, {})

        nonexistent_id = '1234567890'
        self.assertIsNone(await self._simulton_client.get_item(nonexistent_id))
        self.assertIsNone(await self._simulton_client.del_item(nonexistent_id))
        return

    async def test_load_simulton(self) -> None:
        """
        Test simulation creation from dict
        python3 -m unittest -k test_load_simulton tests/simulation_test.py
        """
        log.info('test_load_simulton running')
        params = {
            'src_path': 'simultons/clocks_simulton.py',
            'instances': [
                {'name': 'clock-A', 'latency': 0.1},
                {'name': 'clock-B', 'latency': 0.2},
                {'name': 'clock-C', 'latency': 0.3},
            ],
        }
        self._simulton_client = await self._client.load_simulton(params)
        self.assertIsInstance(self._simulton_client, SimultonClient)
        assert self._simulton_client is not None
        clocks = await self._simulton_client.get_items()
        for clock, param in zip(
            clocks.values(), params['instances'], strict=True
        ):
            log.debug(f'clock: {clock}, param: {param}')
            assert isinstance(clock, dict)
            assert isinstance(param, dict)
            self.assertEqual(clock['name'], param['name'])
            self.assertEqual(clock['latency'], param['latency'])
            self.assertEqual(clock['time'], 0.0)
        return

    async def test_from_file(self) -> None:
        """
        Test simulation creation from dict loaded from file
        python3 -m unittest -k test_from_file tests/simulation_test.py
        """
        log.info('test_from_file running')
        params = load_yaml('tests/simultons.yaml')
        assert isinstance(params, dict)
        assert isinstance(params['simultons'], list)
        res = await self._client.load_simultons(params)
        self.assertEqual(len(params['simultons']), len(res))

        for param, simulton_client in zip(
            params['simultons'], res, strict=True
        ):
            assert isinstance(param, dict)
            self.assertIsInstance(simulton_client, SimultonClient)
            # log.debug(f'param: {param}, simulton_client: {simulton_client}')
            assert simulton_client is not None
            items = await simulton_client.get_items()
            instances = param['instances']
            self.assertIsInstance(instances, list)
            # log.debug(f'instances: {instances}, items: {items}')
            self.assertEqual(len(instances), len(items))
            for instance, clock in zip(instances, items.values(), strict=True):
                log.debug(f'instance: {instance}, clock: {clock}')
                assert isinstance(instance, dict)
                assert isinstance(clock, dict)
                self.assertEqual(instance['name'], clock['name'])
                self.assertEqual(instance['latency'], clock['latency'])
                self.assertEqual(clock['time'], 0.0)

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
            NewSimultonParams(src_path='simultons/clocks_simulton.py')
        )
        assert res is not None
        self._simulton_client = SimultonClient(res)
        self.assertEqual(self._simulton_client._state, 'PAUSED')
        res = await self._simulton_client.get_simulton()
        self.assertEqual(self._simulton_client._state, 'PAUSED')
        clocks = await self._simulton_client.get_items()
        log.info(f'clocks: {clocks}')
        self.assertEqual(clocks, {})
        # ID of the clock that does not exist
        nonexistent_id = '1234567890'
        #
        # verify nonexistent clock access
        #
        self.assertIsNone(await self._simulton_client.get_item(nonexistent_id))
        self.assertIsNone(await self._simulton_client.del_item(nonexistent_id))
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
        clocks = await self._simulton_client.get_items()
        log.info(f'clocks: {clocks}')
        self.assertEqual(len(clocks), len(fast_clocks) + len(slow_clocks))
        self.assertEqual(len(clocks), num_fast_clocks + num_slow_clocks)
        #
        # verify nonexistent clock access
        #
        self.assertIsNone(await self._simulton_client.get_item(nonexistent_id))
        self.assertIsNone(await self._simulton_client.del_item(nonexistent_id))
        #
        # retrieve the clock values
        #
        theFastClockId = next(iter(fast_clocks.keys()))
        rdata = await self.get_time(
            self._simulton_client, theFastClockId, fast_latency
        )
        self.assertEqual(rdata, clocks[theFastClockId])
        self.assertEqual(rdata['time'], 0.0)

        theSlowClockId = next(iter(slow_clocks.keys()))
        rdata = await self.get_time(
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
        duration = 0.3
        await asyncio.sleep(duration)
        # retrieve the theClockId clock
        rdata = await self.get_time(
            self._simulton_client, theFastClockId, fast_latency
        )
        assert isinstance(rdata, dict)
        self.assertGreater(rdata['time'], duration + fast_latency)
        log.info(f'slept for {duration} secs, clock: {rdata["time"]}')

        times = 10
        for _ in range(times):
            # pause it
            self.assertTrue(self._client.pause())
            # start it at normal rate
            self.assertTrue(self._client.run())
            # sleep for a pre-defined period
            await asyncio.sleep(duration)

        # retrieve the theClockId clock
        rdata = await self.get_time(
            self._simulton_client, theFastClockId, fast_latency
        )
        self.assertGreater(rdata['time'], duration)
        total = (duration + fast_latency) * (times + 1)
        log.info(f'slept for {total} secs clock {rdata["time"]}')

        self.assertIsNone(await self._simulton_client.get_item(nonexistent_id))
        self.assertIsNone(await self._simulton_client.del_item(nonexistent_id))

        self.assertTrue(await self._simulton_client.del_item(theFastClockId))

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

    async def test_many_simultons(self) -> None:
        """
        Test N simultons

        To run this test alone:
        python3 -m unittest -k test_many_simultons tests/simulation_test.py
        To watch the simulton processes:
            1. use `ps` or `echo $$` to identify the pid of the shell;
            2. then `watch -c -n 0.1 pstree -p <shell-pid> -Ut`
            on MacOS `watch -c -n 0.1 pstree -p 65673 -g 3`
        """
        N = 15

        assert self._client is not None
        sim = self._client.get_simulation()
        assert isinstance(sim, SimulationResponse)
        self.assertEqual(sim.state, 'PAUSED')
        self.assertEqual(sim.rate, 0)
        self.assertTrue(sim.port)

        simultons = self._client.get_simultons()
        expected: dict[str, Any] = {}
        self.assertEqual(simultons, expected)
        #
        # create a few clock simultons
        #
        start = time.time()
        sims = await self.create_clocks_simultons(N)
        dt = time.time() - start
        log.info(f'Created {N} simultons in {dt:.2f} secs')
        #
        # basic simulton verification
        #
        simultons = self._client.get_simultons()
        assert isinstance(simultons, dict)
        self.assertEqual(len(simultons), len(sims))
        self.assertIsInstance(simultons, dict)
        self.assertEqual(len(simultons), len(sims))
        for id, s in simultons.items():
            self.assertEqual(s, sims[int(id)])
        #
        # do something, e.g.:
        #   start running simulation
        #   pause simulation
        #   start simulation at x2 rate
        #   pause simulation
        #
        duration = 1
        await asyncio.sleep(duration)
        log.info(f'Enjoying {N} simultons for {duration} secs')
        #
        #  verify that the clock time did not change
        #
        return
