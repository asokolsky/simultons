#
# HTTP Client Test
#
# Launch it by issuing:
#  python3 -m unittest -v tests/restc_test
#
import asyncio
import time
import unittest
from contextlib import suppress
from json import loads

import httpx

from simultons import async_rest_client, rest_client, setup_logging

log = setup_logging(__name__)

uris = [
    '/ip',
    '/html',
    '/cookies',
    '/dump/request',
    '/gzip',
    # '/image',
    '/user-agent',
    '/get',
    '/headers',
    '/json',
    '/uuid',
]
user_agent = ['python-httpx/' + httpx.__version__]


class TestAsyncRestC(unittest.IsolatedAsyncioTestCase):
    """
    Test HTTP client.
    We test the client against http://httpbin.org
    Here is what you can do:
    https://github.com/dcos/examples/tree/master/httpbin/1.9#use-httpbin
    """

    async def asyncSetUp(self) -> None:
        """
        Executed prior to each test.
        """
        log.info('asyncSetUp')
        self.host = 'httpbin.io'
        port = 80
        verbose = True
        dumpHeaders = False
        self.restc: rest_client | None = rest_client(
            self.host, port, verbose, dumpHeaders
        )
        self.arestc: async_rest_client | None = async_rest_client(
            self.host, port, verbose, dumpHeaders
        )
        return

    async def asyncTearDown(self) -> None:
        """
        Executed after each test
        """
        log.info('asyncTearDown')
        if self.restc is not None:
            self.restc.close()
            self.restc = None
        if self.arestc is not None:
            with suppress(RuntimeError):
                await self.arestc.close()
            self.arestc = None
        return

    def test_get(self) -> None:
        """
        Test rest_client.get
        """
        uri = '/ip'
        assert self.restc is not None
        (status_code, rdata) = self.restc.get(uri)
        self.assertEqual(status_code, 200)
        self.assertEqual(len(rdata), 1)
        self.assertIn('origin', rdata)

        uri = '/user-agent'
        (status_code, rdata) = self.restc.get(uri)
        self.assertEqual(status_code, 200)
        self.assertEqual(len(rdata), 1)
        self.assertIn('user-agent', rdata)
        ua = rdata['user-agent']
        self.assertTrue(ua.startswith('python'))

        uri = '/get'
        (status_code, rdata) = self.restc.get(uri)
        self.assertEqual(status_code, 200)
        expected = {
            'args': {},
            'headers': {
                'Accept': ['*/*'],
                'Accept-Encoding': ['gzip, deflate'],
                'Connection': ['keep-alive'],
                'Host': [self.host],
                'User-Agent': user_agent,
            },
            'method': 'GET',  # optional
            'origin': '1.8.9.1:37470',
            'url': f'http://{self.host}/get',
        }
        self.assertEqual(len(rdata), len(expected))
        for hdr in ('args', 'method', 'url'):
            self.assertEqual(rdata[hdr], expected[hdr])
        self.assertIn('origin', rdata)
        self.assertIn('headers', rdata)
        headers = rdata['headers']
        assert isinstance(headers, dict)
        assert isinstance(expected['headers'], dict)
        # self.assertEqual(len(headers), 6)
        for hdr in ('Accept', 'Accept-Encoding', 'Host', 'User-Agent'):
            self.assertEqual(headers[hdr], expected['headers'][hdr])

        # self.assertIn('Cache-Control', headers)
        # self.assertIn('If-Modified-Since', headers)
        return

    def test_post(self) -> None:
        """
        Test rest_client.post
        """
        uri = '/post'
        da = {
            'a': 'value-of-a',
            'b': 1234,
            'c': {'d': ['I', 'love', 'REST'], 'e': 'done'},
        }
        assert self.restc is not None
        (status_code, rdata) = self.restc.post(uri, da)
        self.assertEqual(status_code, 200)
        expected = {
            'args': {},
            'headers': {
                'Accept': ['*/*'],
                'Accept-Encoding': ['gzip, deflate'],
                'Connection': ['keep-alive'],
                'Content-Length': ['78'],
                'Content-Type': ['application/json'],
                'Host': [self.host],
                'User-Agent': user_agent,
            },
            'method': 'POST',
            'origin': '1.8.9.1:57320',
            'url': 'http://httpbin.io/post',
            'data': '{"a": "value-of-a", ... "e": "done"}}',
            'files': {},
            'form': {},
            'json': {
                'a': 'value-of-a',
                'b': 1234,
                'c': {'d': ['I', 'love', 'REST'], 'e': 'done'},
            },
        }
        self.assertEqual(len(rdata), len(expected))
        for hdr in ('args', 'method', 'files', 'url'):
            self.assertEqual(rdata[hdr], expected[hdr])
        self.assertIn('data', rdata)
        self.assertEqual(loads(rdata['data']), da)
        self.assertIn('origin', rdata)

        self.assertIn('headers', rdata)
        headers = rdata['headers']
        assert isinstance(headers, dict)
        assert isinstance(expected['headers'], dict)
        # self.assertEqual(len(headers), 6)
        for hdr in ('Accept', 'Accept-Encoding', 'Host', 'User-Agent'):
            self.assertEqual(headers[hdr], expected['headers'][hdr])

        # self.assertIn('Cache-Control', headers)
        # self.assertIn('If-Modified-Since', headers)
        return

    def test_delete(self) -> None:
        """
        Test rest_client.delete
        """
        uri = '/delete'
        assert self.restc is not None
        (status_code, rdata) = self.restc.delete(uri)
        self.assertEqual(status_code, 200)
        expected = {
            'args': {},
            'headers': {
                'Accept': ['*/*'],
                'Accept-Encoding': ['gzip, deflate'],
                'Connection': ['keep-alive'],
                'Content-Length': ['0'],
                'Host': [self.host],
                'User-Agent': user_agent,
            },
            'method': 'DELETE',
            'origin': '1.8.9.1:42064',
            'url': f'http://{self.host}/delete',
            'data': '',
            'files': {},
            'form': {},
            'json': None,
        }
        self.assertEqual(len(rdata), len(expected))
        for hdr in ('args', 'method', 'data', 'files', 'form', 'json', 'url'):
            self.assertEqual(rdata[hdr], expected[hdr])

        self.assertIn('headers', rdata)
        headers = rdata['headers']
        assert isinstance(headers, dict)
        assert isinstance(expected['headers'], dict)
        for hdr in ('Accept', 'Accept-Encoding', 'Host', 'User-Agent'):
            self.assertEqual(headers[hdr], expected['headers'][hdr])
        return

    def test_put(self) -> None:
        """
        Test rest_client.put
        """
        uri = '/put'
        da = {
            'a': 'value-of-a',
            'b': 1234,
            'c': {'d': ['I', 'love', 'REST'], 'e': 'done'},
        }
        assert self.restc is not None
        (status_code, rdata) = self.restc.put(uri, da)
        self.assertEqual(status_code, 200)
        expected = {
            'args': {},
            'headers': {
                'Accept': ['*/*'],
                'Accept-Encoding': ['gzip, deflate'],
                'Connection': ['keep-alive'],
                'Content-Length': ['78'],
                'Content-Type': ['application/json'],
                'Host': [self.host],
                'User-Agent': user_agent,
            },
            'method': 'PUT',
            'origin': '1.8.9.1:55592',
            'url': 'http://httpbin.io/put',
            'data': '{"a": "value-of-a", ... "e": "done"}}',
            'files': {},
            'form': {},
            'json': {
                'a': 'value-of-a',
                'b': 1234,
                'c': {'d': ['I', 'love', 'REST'], 'e': 'done'},
            },
        }
        self.assertEqual(len(rdata), len(expected))
        for hdr in ('args', 'method', 'files', 'form', 'json', 'url'):
            self.assertEqual(rdata[hdr], expected[hdr], hdr)
        self.assertEqual(loads(rdata['data']), da)
        self.assertIn('origin', rdata)
        self.assertIn('headers', rdata)
        headers = rdata['headers']
        assert isinstance(headers, dict)
        assert isinstance(expected['headers'], dict)
        for hdr in ('Accept', 'Accept-Encoding', 'Host', 'User-Agent'):
            self.assertEqual(headers[hdr], expected['headers'][hdr])
        return

    def test_patch(self) -> None:
        """
        Test rest_client.patch
        """
        uri = '/patch'
        da = {
            'a': 'value-of-a',
            'b': 1234,
            'c': {'d': ['I', 'love', 'REST'], 'e': 'done'},
        }
        assert self.restc is not None
        (status_code, rdata) = self.restc.patch(uri, da)
        self.assertEqual(status_code, 200)
        expected = {
            'args': {},
            'headers': {
                'Accept': ['*/*'],
                'Accept-Encoding': ['gzip, deflate'],
                'Connection': ['keep-alive'],
                'Content-Length': ['78'],
                'Content-Type': ['application/json'],
                'Host': [self.host],
                'User-Agent': user_agent,
            },
            'method': 'PATCH',
            'origin': '151.83.9.13:38166',
            'url': 'http://httpbin.io/patch',
            'data': '{"a": "value-of-a", ... "e": "done"}}',
            'files': {},
            'form': {},
            'json': {
                'a': 'value-of-a',
                'b': 1234,
                'c': {'d': ['I', 'love', 'REST'], 'e': 'done'},
            },
        }
        self.assertEqual(len(rdata), len(expected))
        for hdr in ('args', 'method', 'files', 'form', 'json', 'url'):
            self.assertEqual(rdata[hdr], expected[hdr])
        self.assertEqual(loads(rdata['data']), da)
        self.assertIn('origin', rdata)
        self.assertIn('headers', rdata)
        headers = rdata['headers']
        assert isinstance(headers, dict)
        assert isinstance(expected['headers'], dict)
        for hdr in ('Accept', 'Accept-Encoding', 'Host', 'User-Agent'):
            self.assertEqual(headers[hdr], expected['headers'][hdr])
        return

    async def test_multiple_gets_parallel(self) -> None:
        """
        Try rest_client.get in parallel.
        To run just this test:
        python3 -m unittest -k test_multiple_gets_p tests/restc_test.py
        """
        log.info(f'Retrieving {len(uris)} URIs in parallel')
        start = time.time()

        assert self.arestc is not None
        results = await asyncio.gather(*(self.arestc.get(uri) for uri in uris))

        elapsed = time.time() - start
        log.info(f'Retrieved {len(uris)} URIs in {elapsed:.2f} secs')
        log.info(f'asyncio.gather => {results}')

        # produces:
        # Retrieved 6 URIs in 1.043 secs
        return

    def test_multiple_gets_sequential(self) -> None:
        """
        To run just this test:
        python3 -m unittest -k test_multiple_gets_s tests/restc_test.py
        """
        log.info(f'Retrieving {len(uris)} URIs sequentially')
        start = time.time()

        assert self.restc is not None
        for uri in uris:
            self.restc.get(uri)

        elapsed = time.time() - start
        log.info(f'Retrieved {len(uris)} URIs in {elapsed:.2f} secs')

        # produces:
        # Retrieved 6 URIs in 4.805 secs
        return


if __name__ == '__main__':
    unittest.main()
