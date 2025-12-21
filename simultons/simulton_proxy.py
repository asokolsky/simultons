from pathlib import Path

from . import (
    FastLauncher,
    Simulton,
    SimultonRequest,
    SimultonResponse,
    SimultonState,
    api_simulton,
    async_rest_client,
    rest_client,
    setup_logging,
)

log = setup_logging(__name__)


class SimultonProxy(Simulton):
    """
    SimultonProxy is used by the simulation to talk to the simultons
    and is simulation's idea of simulton(s) which live in their own process.
    """

    def __init__(self, source_path: str, port: int) -> None:
        super().__init__()
        self._launcher = FastLauncher(source_path, port)
        self.description = ''
        self.endpoint = ''
        self.title = ''
        self.rate = self._rate
        self.state = self._state
        self.version = ''
        return

    @property
    def path(self) -> Path:
        """Path accessor"""
        return self._launcher._path

    @property
    def port(self) -> int:
        """Port accessor"""
        return self._launcher.port

    @property
    def restc(self) -> rest_client:
        """
        REST client to talk to the simulton
        """
        assert self._launcher is not None
        return self._launcher._restc

    @property
    def arestc(self) -> async_rest_client:
        """
        Async REST client to talk to the simulton
        """
        assert self._launcher is not None
        return self._launcher._arestc

    def to_response(self) -> SimultonResponse:
        return SimultonResponse(
            description=self.description,
            endpoint=self.endpoint,
            port=self.port,
            rate=self.rate,
            state=self.state,
            title=self.title,
            version=self.version,
        )

    def launch(self) -> int:
        """
        Launch the simulton process
        """
        log.debug(f'SimultonProxy.launch({self})')
        return self._launcher.launch()

    def wait_until_reachable(self, timeout: int = 20) -> bool:
        """
        Side-effect: sets the attributes
        """
        log.debug(f'SimultonProxy.wait_until_reachable({api_simulton})')
        jresp = self._launcher.wait_until_reachable(api_simulton, timeout)
        log.debug(
            f'SimultonProxy.wait_until_reachable({api_simulton}) => {jresp}'
        )
        assert isinstance(jresp, dict)
        self.description = jresp['description']
        self.endpoint = jresp['endpoint']
        self.rate = jresp['rate']
        self.title = jresp['title']
        self.version = jresp['version']
        self.state = jresp['state']
        return True

    def pause(self) -> bool:
        """
        Send a blocking! request to the simulton to move to the PAUSED state.
        For use in tests ONLY!
        """
        log.debug('SimultonProxy.pause()')
        params = SimultonRequest(state=SimultonState.PAUSED)
        (status_code, _) = self.restc.put(api_simulton, params.model_dump())
        return status_code == 202

    def run(self, rate: float = 1.0) -> bool:
        """
        Send a blocking! request to the simulton to move to the RUNNING state.
        For use in tests ONLY!
        """
        log.debug(f'SimultonProxy.run({rate})')
        params = SimultonRequest(state=SimultonState.RUNNING, rate=rate)
        (status_code, _) = self.restc.put(api_simulton, params.model_dump())
        return status_code == 202

    def shutting(self) -> bool:
        """
        Send a blocking! request to the simulton to move to the SHUTTING state.
        For use in tests ONLY!
        """
        log.debug('SimultonProxy.shutting')
        params = SimultonRequest(state=SimultonState.SHUTTING)
        (status_code, _) = self.restc.put(api_simulton, params.model_dump())
        return status_code == 202

    def shutdown(self) -> None:
        """
        Forcefully shut the simulton process
        """
        log.debug('SimultonProxy.shutdown')
        self._launcher.shutdown(timeout=1)
        return

    def wait_to_die(self, timeout: float = 0.5) -> bool:
        log.debug(f'SimultonProxy.wait_to_die({timeout})')
        return self._launcher.wait_to_die(timeout=timeout)
