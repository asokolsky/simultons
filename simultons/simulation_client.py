"""
Simulation REST client in python
"""

import asyncio
import time
from types import TracebackType
from typing import Any, Self

import httpx

from simultons import (
    FastLauncher,
    NewSimultonParams,
    SimulationRequest,
    SimulationResponse,
    SimulationState,
    SimultonClient,
    SimultonResponse,
    api_simulation,
    api_simultons,
    async_rest_client,
    load_yaml,
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
        self._launcher: FastLauncher | None = None
        # TODO: verify settings schema
        self._settings = load_yaml(fname)
        log.debug(f'SimulationClient: {self._settings}')
        return

    @property
    def url(self) -> str:
        """
        URL of the simulation service.
        """
        assert self._launcher is not None
        return self._launcher.url

    @property
    def restc(self) -> rest_client:
        assert self._launcher is not None
        assert self._launcher._restc is not None
        return self._launcher._restc

    @property
    def arestc(self) -> async_rest_client:
        assert self._launcher is not None
        assert self._launcher._arestc is not None
        return self._launcher._arestc

    def set_up(self, port: int | None = None) -> bool:
        """
        Launch simulation process.
        port overrides settings.yaml — pass find_free_port() for test isolation.
        """
        if self._settings is None:
            log.debug('SimulationClient.set_up => False')
            return False
        log.debug(f'SimulationClient.set_up settings: {self._settings}')
        assert isinstance(self._settings, dict)
        sim_settings = self._settings['simulation']
        assert isinstance(sim_settings, dict)
        if port is None:
            port = sim_settings['port']
        source = sim_settings['source']
        self._launcher = FastLauncher(source, port)
        pid = self._launcher.launch()
        log.debug(f'FastLauncher({source}, {port}).launch() => {pid}')
        res = self._launcher.wait_until_reachable(api_simulation)
        log.debug(f'wait_until_reachable({api_simulation}) => {res}')
        assert res is not None
        assert res['state'] == SimulationState.PAUSED
        assert res['rate'] == 0.0
        assert res['port']
        return True

    async def tear_down(self) -> None:
        """
        Request simulation process shutdown.
        """
        log.debug('tear_down')
        if self._launcher is None:
            return

        req = SimulationRequest(state=SimulationState.SHUTTING)
        res = self.put_simulation(req)
        log.debug(f'self.put_simulation({req}) => {res}')
        await self._launcher.close_sockets()
        self._launcher.wait_to_die(2)
        await self._launcher.shutdown(3)
        self._launcher = None
        return

    async def __aenter__(self) -> Self:
        """
        Enter the with block, start the CLI session
        """
        log.info('SimulationClient.__enter__()')
        self.set_up()
        return self

    async def __aexit__(
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
        await self.tear_down()
        return

    def get_simulation(self) -> SimulationResponse | None:
        """
        Issue an HTTP GET to the simulation
        """
        try:
            (status_code, rdata) = self.restc.get(api_simulation)
            assert status_code == 200
            assert isinstance(rdata, dict)
            return SimulationResponse(**rdata)
        except httpx.ConnectError as err:
            log.warning(f'Caught in SimulationClient.get_simulation: {err}')
        except httpx.ReadTimeout as err:
            log.warning(f'Caught in SimulationClient.get_simulation: {err}')
        return None

    def put_simulation(
        self, req: SimulationRequest
    ) -> SimulationResponse | None:
        """
        Request simulation state change
        """
        try:
            (status_code, rdata) = self.restc.put(
                api_simulation, req.model_dump()
            )
            assert status_code == 202
            assert isinstance(rdata, dict)
            return SimulationResponse(**rdata)
        except httpx.ConnectError as err:
            log.info(f'Caught in SimulationClient.put_simulation: {err}')
        except httpx.ReadTimeout as err:
            log.info(f'Caught in SimulationClient.put_simulation: {err}')
        return None

    def pause(self) -> bool:
        """
        Send a blocking! request to the simulation to move it into the PAUSED state.
        """
        log.debug('pause()')
        resp = self.put_simulation(
            SimulationRequest(state=SimulationState.PAUSED)
        )
        return resp is not None

    def run(self, rate: float = 1.0) -> bool:
        """
        Send a blocking! request to the simulation to move it into the RUNNING state.
        """
        log.debug(f'run({rate})')
        resp = self.put_simulation(
            SimulationRequest(state=SimulationState.RUNNING, rate=rate)
        )
        return resp is not None

    def post_simulton(
        self, params: NewSimultonParams
    ) -> SimultonResponse | None:
        """
        Request creation of new simulton.
        Optionally wait until it is available.
        """
        (status_code, rdata) = self.restc.post(
            api_simultons, params.model_dump()
        )
        assert status_code == 201
        if status_code != 201:
            return None
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
        return SimultonResponse(**rdata)

    async def async_post_simulton(
        self, params: NewSimultonParams
    ) -> SimultonResponse | None:
        """
        Request creation of new simulton.
        Optionally wait until it is available.
        """
        (status_code, rdata) = await self.arestc.post(
            api_simultons, params.model_dump()
        )
        assert status_code == 201
        assert isinstance(rdata, dict)
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
        return SimultonResponse(**rdata)

    def get_simultons(self) -> dict[int, SimultonResponse] | None:
        """
        Request a list of simultons
        """
        (status_code, rdata) = self.restc.get(api_simultons)
        assert status_code == 200, f'expected: 200, got: {status_code} {rdata}'
        assert isinstance(rdata, dict)
        return {key: SimultonResponse(**val) for key, val in rdata.items()}

    def get_simulton(self, id: Any) -> SimultonResponse | None:
        """
        Request a list of simultons
        """
        (status_code, rdata) = self.restc.get(f'{api_simultons}/{id}')
        if status_code == 200:
            assert isinstance(rdata, dict)
            return SimultonResponse(**rdata)
        log.info(f'get_simulton({id}) failed - {status_code}')
        return None

    async def load_simulton(self, sim: dict) -> SimultonClient | None:
        """
        Load the simulton from dict, which comes from a YAML file.
        """
        instances = sim.get('instances', [])
        src_path = sim.get('src_path')
        if src_path is None:
            log.warning(f'load_simulton: missing `src_path` in {sim}')
            return None
        resp = self.post_simulton(NewSimultonParams(src_path=src_path))
        log.debug(f'load_simulton: created {resp}')
        assert resp is not None
        client = SimultonClient(resp)
        if instances:
            await client.new_items(instances)
        return client

    async def load_simultons(self, sims: dict) -> list[SimultonClient | None]:
        """
        Load simultons from dict, which comes from a YAML file.
        """
        log.debug(f'load_simultons: {sims}')
        params = sims.get('simultons', [])
        if not params:
            log.warning(f'load_simultons: missing `simultons` in {sims}')
            return []
        tasks = [self.load_simulton(param) for param in params]
        start = time.time()
        res = await asyncio.gather(*tasks)
        dt = time.time() - start
        log.info(f'Created {len(res)} simultons in {dt:.2f} secs')
        return res
