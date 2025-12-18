"""
Simulation REST client in python
"""

import time
from types import TracebackType
from typing import Any

import httpx

from simultons import (
    FastLauncher,
    NewSimultonParams,
    SimulationRequest,
    SimulationState,
    api_simulation,
    api_simultons,
    load_settings,
    rest_client,
    setup_logging,
)

log = setup_logging(__name__)


class SimulationClient:
    """
    Python client to talk to the simulation using REST API.
    """

    def __init__(self, fname: str = 'settings.yaml') -> None:
        log.debug(f'SimulationClient: {fname}')
        self._service: FastLauncher | None = None
        self._restc: rest_client | None = None
        self._settings = load_settings(fname)
        log.debug(f'SimulationClient: {self._settings}')
        return

    def set_up(self) -> bool:
        """
        Launch simulation process.
        """
        if self._settings is None:
            log.debug('SimulationClient.set_up => False')
            return False
        log.debug(f'SimulationClient.set_up settings: {self._settings}')
        assert isinstance(self._settings, dict)
        sim_settings = self._settings['simulation']
        assert isinstance(sim_settings, dict)
        port = sim_settings['port']
        source = sim_settings['source']
        self._service = FastLauncher(source, port)
        pid = self._service.launch()
        log.debug(f'FastLauncher({source}, {port}).launch() => {pid}')
        res = self._service.wait_until_reachable(api_simulation)
        log.debug(f'wait_until_reachable({api_simulation}) => {res}')
        expected = {'state': 'PAUSED', 'rate': 0.0}
        assert res == expected
        #
        # create simulation REST client
        #
        verbose = True
        dumpHeaders = False
        self._restc = self._service.get_rest_client(verbose, dumpHeaders)
        return True

    def tear_down(self) -> None:
        """
        Request simulation process shutdown.
        """
        log.debug('tear_down')
        if self._service is not None:
            req = SimulationRequest(state=SimulationState.SHUTTING)
            if self.put_simulation(req) is not None:
                time.sleep(0.01)
                self._service.wait_to_die(5)
            self._service.shutdown(timeout=3)
            self._service = None
        # self.restc.close()
        self._restc = None
        return

    def __enter__(self) -> 'SimulationClient':
        """
        Enter the with block, start the CLI session
        """
        log.info('SimulationClient.__enter__()')
        self.set_up()
        return self

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception_value: BaseException | None,
        exception_traceback: TracebackType | None,
    ) -> None:
        """
        Handle the exception(s)
        """
        log.info(
            f'SimulationClient.__exit__({exception_type}, {exception_value}, {exception_traceback})'
        )
        self.tear_down()
        return

    def get_simulation(self) -> dict | None:
        """
        Issue an HTTP GET to the simulation
        """
        if self._restc is None:
            log.info('get_simulation failed - _restc is None')
            return None
        try:
            (status_code, rdata) = self._restc.get(api_simulation)
            assert status_code == 200
            assert isinstance(rdata, dict)
            return rdata
        except httpx.ConnectError as err:
            log.warning(f'Caught in SimulationClient.get_simulation: {err}')
        except httpx.ReadTimeout as err:
            log.warning(f'Caught in SimulationClient.get_simulation: {err}')
        return None

    def put_simulation(self, req: SimulationRequest) -> dict | None:
        """
        Request simulation state change
        """
        if self._restc is None:
            log.info('put_simulation failed - _restc is None')
            return None
        assert self._service is not None
        try:
            (_, rdata) = self._restc.put(api_simulation, req.model_dump())
            assert isinstance(rdata, dict)
            return rdata
        except httpx.ConnectError as err:
            log.info(f'Caught in SimulationClient.put_simulation: {err}')
        except httpx.ReadTimeout as err:
            log.info(f'Caught in SimulationClient.put_simulation: {err}')
        return None

    def post_simulton(self, params: NewSimultonParams) -> dict | None:
        """
        Request creation of new simulton
        """
        if self._restc is None:
            log.info('post_simulton failed - _restc is None')
            return None
        (status_code, rdata) = self._restc.post(api_simultons, params.model_dump())
        assert status_code == 201
        assert isinstance(rdata, dict)
        return rdata

    def get_simultons(self) -> dict | None:
        """
        Request a list of simultons
        """
        if self._restc is None:
            log.info('get_simultons failed - _restc is None')
            return None
        (status_code, rdata) = self._restc.get(api_simultons)
        assert status_code == 200
        assert isinstance(rdata, dict)
        return rdata

    def get_simulton(self, id: Any) -> dict | None:
        """
        Request a list of simultons
        """
        if self._restc is None:
            log.info(f'get_simulton({id}) failed - _restc is None')
        else:
            (status_code, rdata) = self._restc.get(f'{api_simultons}/{id}')
            if status_code == 200:
                assert isinstance(rdata, dict)
                return rdata
            log.info(f'get_simulton({id}) failed - {status_code}')
        return None
