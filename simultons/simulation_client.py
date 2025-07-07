"""
Simulation REST client in python
"""

import time

import httpx

from simultons import (
    FastLauncher,
    NewSimultonParams,
    SimulationRequest,
    SimulationState,
    load_settings,
    rest_client,
)


class SimulationClient:
    """
    Python client to talk to the simulation using REST API.
    """

    api_uri = '/api/v1/simulation'
    simultons_uri = '/api/v1/simultons'

    def __init__(self) -> None:
        self._service: FastLauncher | None = None
        self._restc: rest_client | None = None
        return

    def setUp(self) -> None:
        self._settings = load_settings()
        print('settings:', self._settings)
        assert isinstance(self._settings, dict)
        sim_settings = self._settings['simulation']
        assert isinstance(sim_settings, dict)
        port = sim_settings['port']
        source = sim_settings['source']
        self._service = FastLauncher(source, port)
        pid = self._service.launch()
        print(f'FastLauncher({source}, {port}).launch() => ', pid)
        res = self._service.wait_until_reachable(self.api_uri)
        print(f'wait_until_reachable({self.api_uri}) => ', res)
        expected = {'state': 'PAUSED', 'rate': 0.0}
        assert res == expected
        #
        # create simulation REST client
        #
        verbose = True
        dumpHeaders = False
        self._restc = self._service.get_rest_client(verbose, dumpHeaders)
        return

    def tearDown(self) -> None:
        # request simulation process shutdown
        assert self._service is not None
        req = SimulationRequest(state=SimulationState.SHUTTING)
        if self.put_simulation(req) is not None:
            self._service.wait_to_die(5)
        time.sleep(0.1)
        self._service.shutdown(timeout=3)
        self._service = None
        # self.restc.close()
        self._restc = None
        return

    def get_simulation(self) -> dict | None:
        if self._restc is None:
            print('get_simulation failed - _restc is None')
            return None
        try:
            (status_code, rdata) = self._restc.get(self.api_uri)
            assert status_code == 200
            assert isinstance(rdata, dict)
            return rdata
        except httpx.ConnectError as err:
            print('Caught in SimulationClient.get_simulation:', err)
        except httpx.ReadTimeout as err:
            print('Caught in SimulationClient.get_simulation:', err)
        return None

    def put_simulation(self, req: SimulationRequest) -> dict | None:
        """
        Request simulation state change
        """
        if self._restc is None:
            print('put_simulation failed - _restc is None')
            return None
        assert self._service is not None
        try:
            (status_code, rdata) = self._restc.put(self.api_uri, req.model_dump())
            assert isinstance(rdata, dict)
            self._service.wait_to_die(5)
            return rdata
        except httpx.ConnectError as err:
            print('Caught in SimulationClient.put_simulation:', err)
        except httpx.ReadTimeout as err:
            print('Caught in SimulationClient.put_simulation:', err)
        return None

    def post_simulton(self, params: NewSimultonParams) -> dict | None:
        """
        Request creation of new simulton
        """
        if self._restc is None:
            print('post_simulton failed - _restc is None')
            return None
        (status_code, rdata) = self._restc.post(self.simultons_uri, params.model_dump())
        assert status_code == 201
        assert isinstance(rdata, dict)
        return rdata

    def get_simultons(self) -> dict | None:
        """
        Request a list of simultons
        """
        if self._restc is None:
            print('get_simultons failed - _restc is None')
            return None
        (status_code, rdata) = self._restc.get(self.simultons_uri)
        assert status_code == 200
        assert isinstance(rdata, dict)
        return rdata
