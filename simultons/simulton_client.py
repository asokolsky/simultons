import asyncio
from contextlib import suppress
from typing import Any

from . import (
    SimultonResponse,
    api_simulton,
    async_rest_client,
    rest_client,
    setup_logging,
    wait_until_reachable,
)

log = setup_logging(__name__)


class SimultonClient:
    """
    High'er level abstraction for communication with Simulton.
    """

    def __init__(self, resp: SimultonResponse) -> None:
        log.debug(f'SimultonClient(resp={resp})')
        self._host = '127.0.0.1'
        self._description = resp.description
        assert isinstance(self._description, str)
        self._endpoint = resp.endpoint
        assert isinstance(self._endpoint, str)
        self._port = resp.port
        assert isinstance(self._port, int)
        self._rate = resp.rate
        assert isinstance(self._rate, float)
        self._state = resp.state
        assert isinstance(self._state, str)
        self._title = resp.title
        assert isinstance(self._title, str)
        self._version = resp.version
        assert isinstance(self._version, str)
        #
        # control REST client verbosity
        #
        verbose = True
        dumpHeaders = False
        self._arestc: async_rest_client | None = async_rest_client(
            self._host, self._port, verbose, dumpHeaders
        )
        self._restc: rest_client | None = rest_client(
            self._host, self._port, verbose, dumpHeaders
        )
        return

    async def close(self) -> None:
        """
        Close the REST client connections.
        """
        if self._restc is not None:
            self._restc.close()
            self._restc = None
        if self._arestc is not None:
            with suppress(RuntimeError):
                await self._arestc.close()
            self._arestc = None
        return

    @property
    def url(self) -> str:
        """
        URL of the simulton REST service.
        """
        return f'http://{self._host}:{self._port}{self._endpoint}'

    def wait_until_reachable(self) -> None:
        """
        Wait for the Simulton to finish start-up
        """
        url = f'http://{self._host}:{self._port}{api_simulton}'
        res = wait_until_reachable(url)
        log.debug(f'wait_until_reachable({url}) => {res}')
        assert res is not None
        return

    async def get_simulton(self) -> SimultonResponse:
        """
        Retrieve the SimultonResponse
        """
        assert self._arestc is not None
        (status_code, rdata) = await self._arestc.get(api_simulton)
        assert status_code == 200
        log.debug(f'SimultonClient.get_simulton() => {rdata}')

        assert isinstance(rdata, dict)
        assert self._description == rdata['description']
        assert self._endpoint == rdata['endpoint']
        assert self._port == rdata['port']
        self._rate = rdata['rate']
        assert isinstance(self._rate, float)
        self._state = rdata['state']
        assert isinstance(self._state, str)
        assert self._title == rdata['title']
        assert self._version == rdata['version']
        return SimultonResponse(**rdata)

    async def get_collection(self) -> dict[str, dict]:
        """
        Retrieve the collection of objects from the Simulton service.
        """
        assert self._arestc is not None
        (status_code, rdata) = await self._arestc.get(self._endpoint)
        assert status_code == 200
        assert isinstance(rdata, dict)
        return rdata

    async def get_item(self, item_id: str) -> dict | None:
        """
        Retrieve a specific item from the collection.
        """
        assert self._arestc is not None
        uri = f'{self._endpoint}/{item_id}'
        (status_code, rdata) = await self._arestc.get(uri)
        if status_code == 404:
            return None
        assert status_code == 200
        assert isinstance(rdata, dict)
        return rdata

    async def del_item(self, item_id: str) -> dict | None:
        """
        Delete a specific item from the collection.
        """
        assert self._arestc is not None
        uri = f'{self._endpoint}/{item_id}'
        (status_code, rdata) = await self._arestc.delete(uri)
        if status_code == 404:
            return None
        assert status_code == 200
        assert isinstance(rdata, dict)
        return rdata

    async def new_item(self, param: dict) -> tuple[int, Any]:
        """
        Create a new collection item.
        """
        assert self._arestc is not None
        return await self._arestc.post(self._endpoint, param)

    async def new_items(self, params: list[dict]) -> list[tuple[int, Any]]:
        """
        Create a new collection item.
        """
        tasks = [self.new_item(param) for param in params]
        return await asyncio.gather(*tasks)
