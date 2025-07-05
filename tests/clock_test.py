import time
import unittest

from simultons import ClockResponse, NewClockParams, SimultonProxy, rest_client

simulton_uri = '/api/v1/simulton'
clocks_uri = '/api/v1/clocks/'


class TestClockSimulton(unittest.TestCase):
    """
    Verify Simulation Clock Simulton functionality
    """

    _service: SimultonProxy | None = None
    restc: rest_client | None = None

    @classmethod
    def setUpClass(cls) -> None:
        """
        Launch the simulton - usually this is done by the simulation process.
        """
        print('TestClockSimulton.setUpClass')
        cls._service = SimultonProxy('simultons/clock.py', 9000)
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
        Shut the simulton process
        """
        print('TestClockSimulton.tearDownClass')
        # request the shutdown
        assert cls._service is not None
        cls._service.shutting()
        #
        # wait for the process to actually terminate
        #
        cls._service.wait_to_die(0.2)
        #
        # shut the simulton process
        #
        cls._service.shutdown()
        return

    def setUp(self) -> None:
        return

    def tearDown(self) -> None:
        return

    def create_clocks(self, num_clocks: int) -> dict[str, ClockResponse]:
        """
        Returns dict[clockID, ClockResponse]
        """
        res: dict[str, ClockResponse] = {}
        assert self.restc is not None
        for num in range(num_clocks):
            name = f'clock-{num}'
            params = NewClockParams(name=name)
            (status_code, rdata) = self.restc.post(clocks_uri, params.model_dump())
            self.assertEqual(status_code, 201)
            id = rdata['id']
            self.assertTrue(id)
            self.assertEqual(rdata['name'], name)
            time = rdata['time']
            self.assertTrue(str(time))
            res[id] = rdata
        return res

    def get_time(self, clock_id: str) -> ClockResponse:
        assert self.restc is not None
        (status_code, rdata) = self.restc.get(f'{clocks_uri}{clock_id}')
        self.assertEqual(status_code, 200)
        return rdata

    def get_nonexistent_clock(self) -> None:
        assert self.restc is not None
        (status_code, rdata) = self.restc.get(f'{clocks_uri}1234567890')
        self.assertEqual(status_code, 404)
        expected = {'message': 'Item not found'}
        self.assertEqual(expected, rdata)
        return

    def del_nonexistent_clock(self) -> None:
        assert self.restc is not None
        (status_code, rdata) = self.restc.delete(f'{clocks_uri}1234567890')
        self.assertEqual(status_code, 404)
        expected = {'message': 'Item not found'}
        self.assertEqual(expected, rdata)
        return

    def test_one(self) -> None:
        """
        Test the simulation clock functionality
        """
        assert self.restc is not None
        (status_code, rdata) = self.restc.get(clocks_uri)
        self.assertTrue(status_code, 200)
        expected: dict = {}
        self.assertEqual(rdata, expected)

        self.get_nonexistent_clock()
        self.del_nonexistent_clock()

        clocks = self.create_clocks(1)
        print(clocks)
        theClockId = ''
        for id in clocks:
            theClockId = id
            break
        # retrieve the theClockId clock
        rdata = self.get_time(theClockId)
        self.assertEqual(rdata, clocks[theClockId])
        # clock was never started yet
        self.assertEqual(rdata['time'], 0.0)

        # pause it
        assert self._service is not None
        self.assertTrue(self._service.pause())

        # start it at normal rate
        self.assertTrue(self._service.run())

        # sleep for a pre-defined period
        duration = 0.3
        time.sleep(duration)

        # retrieve the theClockId clock
        rdata = self.get_time(theClockId)
        self.assertTrue(rdata['time'] > 0.0)
        self.assertTrue(rdata['time'] > duration)
        print('I slept for', duration, 'clock', rdata['time'])

        times = 10
        for _ in range(10):
            # pause it
            self.assertTrue(self._service.pause())
            # start it at normal rate
            self.assertTrue(self._service.run())
            # sleep for a pre-defined period
            time.sleep(duration)

        # retrieve the theClockId clock
        rdata = self.get_time(theClockId)
        self.assertTrue(rdata['time'] > 0.0)
        self.assertTrue(rdata['time'] > duration)
        print('I slept for', duration * (times + 1), 'clock', rdata['time'])

        self.get_nonexistent_clock()
        self.del_nonexistent_clock()

        # now delete clock theClockId
        (status_code, rdata) = self.restc.delete(f'{clocks_uri}{theClockId}')
        self.assertEqual(status_code, 200)

        self.get_nonexistent_clock()
        self.del_nonexistent_clock()
        return

    def test_many(self) -> None:
        """
        Test the simulation clocks functionality:
        - create N clocks,
        - use a pull of P processes to retrieve current clock time T times
        """
        return
