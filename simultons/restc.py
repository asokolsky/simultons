"""
REST client and other utilities, now based on httpx, not requests
"""

from json.decoder import JSONDecodeError
from typing import Any
from urllib.parse import urljoin

import httpx

from . import setup_logging

log = setup_logging(__name__)


class rest_client:
    """
    REST client based on httpx
    """

    def __init__(self, host: str, port: int, verbose: bool, dumpHeaders: bool) -> None:
        """
        In: iface - server interface, or host name
            port - server port
        """
        self.base_url = f'http://{host}:{port}'
        self.verbose = verbose
        self.dumpHeaders = dumpHeaders
        self.ses = httpx.Client(base_url=self.base_url)
        return

    def close(self) -> None:
        """
        Close the underlying TCP connection
        """
        self.ses.close()
        return

    def print_req(self, method: str, uri: str, data: Any | None) -> None:
        if not self.verbose:
            return
        if data is None:
            data = ''
        log.debug(f'HTTP {method} {urljoin(self.base_url, uri)} {data}...')
        return

    def print_resp(self, method: str, resp: httpx.Response) -> None:
        if self.verbose:
            try:
                jresp = resp.json()
            except JSONDecodeError:
                jresp = resp
            log.debug(f'HTTP {method} => {resp.status_code} {jresp}')
        if self.dumpHeaders:
            log.debug('HTTP Response Headers:')
            for h in resp.headers:
                log.debug(f'   {h}: {resp.headers[h]}')
        return

    def get(self, uri: str) -> tuple[int, Any]:
        """
        Issue HTTP GET to a base_url + uri
        returns (http_status, response_json)
        Throws requests.exceptions.ConnectionError when connection fails
        """
        self.print_req('GET', uri, None)
        resp = self.ses.get(uri)
        self.print_resp('GET', resp)
        try:
            jresp = resp.json()
        except JSONDecodeError:
            jresp = resp
        return (resp.status_code, jresp)

    def post(self, uri: str, data: Any) -> tuple[int, Any]:
        """
        Issue HTTP POST to a base_url + uri
        returns (http_status, response_json)
        Throws requests.exceptions.ConnectionError when connection fails
        """
        self.print_req('POST', uri, data)
        resp = self.ses.post(uri, json=data)
        self.print_resp('POST', resp)
        try:
            jresp = resp.json()
        except JSONDecodeError:
            jresp = resp
        return (resp.status_code, jresp)

    def delete(self, uri: str) -> tuple[int, Any]:
        """
        Issue HTTP DELETE to a base_url + uri
        returns (http_status, response_json)
        Throws requests.exceptions.ConnectionError when connection fails
        """
        self.print_req('DELETE', uri, None)
        resp = self.ses.delete(uri)
        self.print_resp('DELETE', resp)
        try:
            jresp = resp.json()
        except JSONDecodeError:
            jresp = resp
        return (resp.status_code, jresp)

    def put(self, uri: str, data: Any) -> tuple[int, Any]:
        """
        Issue HTTP PUT to a base_url + uri
        returns (http_status, response_json)
        Throws requests.exceptions.ConnectionError when connection fails
        """
        self.print_req('PUT', uri, data)
        resp = self.ses.put(uri, json=data)
        self.print_resp('PUT', resp)
        try:
            jresp = resp.json()
        except JSONDecodeError:
            jresp = resp
        return (resp.status_code, jresp)

    def patch(self, uri: str, data: Any) -> tuple[int, Any]:
        """
        Issue HTTP PATCH to a base_url + uri
        returns (http_status, response_json)
        Throws requests.exceptions.ConnectionError when connection fails
        """
        self.print_req('PATCH', uri, data)
        resp = self.ses.patch(uri, json=data)
        self.print_resp('PATCH', resp)
        try:
            jresp = resp.json()
        except JSONDecodeError:
            jresp = resp
        return (resp.status_code, jresp)
