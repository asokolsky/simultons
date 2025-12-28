import time
import unittest

from simultons import (
    ClockResponse,
    NewClockParams,
    SimultonProxy,
    api_clocks,
    setup_logging,
)

log = setup_logging(__name__)


class TestClocksSimulton(unittest.IsolatedAsyncioTestCase):
    """
    Verify Clocks Simulton functionality
    """

    async def asyncSetUp(self) -> None:
        """
        Launch the simulton - usually this is done by the simulation process.
        """
        log.info('TestClockSimulton.setUpClass')
        self._simulton: SimultonProxy | None = SimultonProxy(
            'simultons/clock.py', 9100
        )
        assert self._simulton.launch()
        assert self._simulton.wait_until_reachable() is not None
        return

    async def asyncTearDown(self) -> None:
        """
        Shut the simulton process
        """
        log.info('TestClockSimulton.tearDownClass')
        # request the shutdown - compare this to
        assert self._simulton is not None
        self._simulton.shutting()
        await self._simulton.close_sockets()
        #
        # wait for the process to actually terminate
        #
        self._simulton.wait_to_die(6)
        #
        # shut the simulton process
        #
        await self._simulton.shutdown()
        return

    async def create_clock(self, num: int, latency: float) -> ClockResponse:
        """
        Create a single clock in the clocks simulton.
        """
        params = NewClockParams(name=f'clock-{num}', latency=latency)
        assert TestClocksSimulton._simulton is not None
        (status_code, rdata) = await TestClocksSimulton._simulton.arestc.post(
            api_clocks, params.model_dump()
        )
        assert status_code == 201
        id = rdata['id']
        assert id
        assert rdata['name'] == 'clock-1'
        time = rdata['time']
        assert str(time)
        return ClockResponse(**rdata)

    def create_clocks(
        self, num_clocks: int, latency: float
    ) -> dict[str, ClockResponse]:
        """
        Create multiple clocks in a single singleton.
        Returns dict[clockID, ClockResponse]
        """
        res: dict[str, ClockResponse] = {}
        assert self._simulton is not None
        assert self._simulton.restc is not None
        for num in range(num_clocks):
            name = f'clock-{num}'
            params = NewClockParams(name=name, latency=latency)
            (status_code, rdata) = self._simulton.restc.post(
                api_clocks, params.model_dump()
            )
            self.assertEqual(status_code, 201)
            id = rdata['id']
            self.assertTrue(id)
            self.assertEqual(rdata['name'], name)
            time = rdata['time']
            self.assertTrue(str(time))
            res[id] = rdata
        return res

    def get_clocks(self) -> dict[str, ClockResponse]:
        assert self._simulton is not None
        assert self._simulton.restc is not None
        (status_code, rdata) = self._simulton.restc.get(api_clocks)
        self.assertEqual(status_code, 200)
        return {k: ClockResponse(**v) for k, v in rdata.items()}

    def del_clocks(self, clocks: dict[str, ClockResponse]) -> None:
        assert self._simulton is not None
        assert self._simulton.restc is not None
        for clock_id in clocks:
            (status_code, _) = self._simulton.restc.delete(
                f'{api_clocks}/{clock_id}'
            )
            self.assertEqual(status_code, 200)
        return

    def get_time(self, clock_id: str) -> ClockResponse:
        assert self._simulton is not None
        assert self._simulton.restc is not None
        (status_code, rdata) = self._simulton.restc.get(
            f'{api_clocks}/{clock_id}'
        )
        self.assertEqual(status_code, 200)
        assert isinstance(rdata, dict)
        return ClockResponse(**rdata)

    def get_nonexistent_clock(self) -> None:
        assert self._simulton is not None
        assert self._simulton.restc is not None
        (status_code, rdata) = self._simulton.restc.get(
            f'{api_clocks}/1234567890'
        )
        self.assertEqual(status_code, 404)
        expected = {'message': 'Item not found'}
        self.assertEqual(expected, rdata)
        return

    def del_nonexistent_clock(self) -> None:
        assert self._simulton is not None
        assert self._simulton.restc is not None
        (status_code, rdata) = self._simulton.restc.delete(
            f'{api_clocks}/1234567890'
        )
        self.assertEqual(status_code, 404)
        expected = {'message': 'Item not found'}
        self.assertEqual(expected, rdata)
        return

    def test_one(self) -> None:
        """
        Test creation of a single Clock in the context of the simulton
        """
        # verify we start with a clean slate
        self.assertEqual(self.get_clocks(), {})

        # self.get_nonexistent_clock()
        # self.del_nonexistent_clock()

        clocks = self.create_clocks(1, 0.0)
        log.info(f'Clocks: {clocks}')
        theClockId = next(iter(clocks.keys()))
        # retrieve the theClockId clock
        rdata = self.get_time(theClockId)
        self.assertEqual(rdata.model_dump(), clocks[theClockId])
        # clock was never started yet
        assert isinstance(rdata, ClockResponse)
        self.assertEqual(rdata.time, 0.0)

        # pause it
        assert self._simulton is not None
        self.assertTrue(self._simulton.pause())

        # start it at normal rate
        self.assertTrue(self._simulton.run())

        # sleep for a pre-defined period
        duration = 0.3
        time.sleep(duration)

        # retrieve the theClockId clock
        rdata = self.get_time(theClockId)
        assert isinstance(rdata, ClockResponse)
        self.assertGreater(rdata.time, duration)
        log.info(f'I slept for {duration} clock {rdata.time}')

        times = 10
        for _ in range(10):
            # pause it
            self.assertTrue(self._simulton.pause())
            # start it at normal rate
            self.assertTrue(self._simulton.run())
            # sleep for a pre-defined period
            time.sleep(duration)

        # retrieve the theClockId clock
        rdata = self.get_time(theClockId)
        self.assertGreater(rdata.time, duration)
        log.info(f'I slept for {duration * (times + 1)} clock {rdata.time}')

        self.get_nonexistent_clock()
        self.del_nonexistent_clock()

        # now delete clock theClockId
        (status_code, rdata) = self._simulton.restc.delete(
            f'{api_clocks}/{theClockId}'
        )
        self.assertEqual(status_code, 200)

        self.get_nonexistent_clock()
        self.del_nonexistent_clock()

        self.del_clocks(self.get_clocks())
        return

    def test_many(self) -> None:
        """
        Test the simulation clocks functionality:
        - create N clocks,
        - use a pull of P processes to retrieve current clock time T times
        """
        # verify we start with a clean slate
        self.assertEqual(self.get_clocks(), {})
        # create clocks of variable latency
        fast_clocks = 5
        fast_latency = 0.1
        clocks_fast = self.create_clocks(fast_clocks, fast_latency)
        log.info(f'clocks_fast: {clocks_fast}')
        slow_clocks = 5
        slow_latency = 0.2
        clocks_slow = self.create_clocks(slow_clocks, slow_latency)
        log.info(f'clocks_slow: {clocks_slow}')
        #
        # retrieve the clocks this should take a long time - cumulative latency
        #
        start = time.time()
        clocks = self.get_clocks()
        dt = time.time() - start
        sequential_time = (fast_clocks * fast_latency) + (
            slow_clocks * slow_latency
        )
        log.info(
            f'clocks: {clocks}, dt: {dt:.2f}, sequential_time: {sequential_time}'
        )
        #
        # Verify the Clocks are being access in parallel, not sequentially!
        #
        self.assertLess(dt, sequential_time)
        #
        # now lets try to reach out to all the clocks in parallel
        #

        # cleanup
        self.del_clocks(self.get_clocks())
        return
