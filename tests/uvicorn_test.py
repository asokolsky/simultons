"""
Test launching/shutting uvicorn/FastAPI server process
"""

import os
import signal
import unittest
from multiprocessing import Process

import fastapi
import uvicorn

from simultons import rest_client, setup_logging, wait_until_reachable

host = '127.0.0.1'
port = 8000

log = setup_logging(__name__)

app = fastapi.FastAPI()


@app.on_event('startup')
async def startup_event() -> None:
    log = setup_logging(__name__)
    log.debug('Server starting up...')
    return


@app.on_event('shutdown')
async def on_shutdown() -> None:
    log.debug('Server shutting down...')
    return


@app.get('/hello')
async def hello() -> dict:
    log.debug('hello')
    return {'message': 'hello world'}


def shut_the_process() -> None:
    os.kill(os.getpid(), signal.SIGTERM)
    # raise KeyboardInterrupt
    return


@app.get('/shutdown')
async def shutdown(background_tasks: fastapi.BackgroundTasks) -> dict:
    """
    An endpoint to shut a FastAPI server
    """
    log.debug('shutdown')
    # os.kill(os.getpid(), signal.SIGTERM)
    background_tasks.add_task(shut_the_process)
    return {'message': 'Server shutting down...'}


def launch_uvicorn() -> None:
    """
    Start FastAPI uvicorn app
    see also:
    https://bugfactory.io/articles/starting-and-stopping-uvicorn-in-the-background/
    """
    log = setup_logging(__name__)
    log.info('launch_uvicorn1')
    uvicorn.run(app, host=host, port=port, workers=1, log_level='debug')
    log.info('launch_uvicorn2')
    return


class TestUvicorn(unittest.TestCase):
    """
    Verify launching/shutting a fastapi process
    """

    process: Process | None = None
    restc = None

    @classmethod
    def setUpClass(cls) -> None:
        """
        Launch uvicorn/FastAPI process
        """
        log.info('setUpClass')
        cls.process = Process(target=launch_uvicorn)
        cls.process.start()
        res = wait_until_reachable(f'http://{host}:{port}/hello')
        assert res is not None

        cls.restc = rest_client(host, port, True, True)  # noqa: FBT003
        return

    @classmethod
    def tearDownClass(cls) -> None:
        """
        Shut uvicorn/FastAPI process
        """
        log.info('tearDownClass')
        assert cls.restc is not None
        (status_code, rdata) = cls.restc.get(f'http://{host}:{port}/shutdown')
        assert cls.process is not None
        cls.process.join()
        return

    def setUp(self) -> None:
        log.info('setUp')
        return

    def tearDown(self) -> None:
        log.info('tearDown')
        return

    def test_all(self) -> None:
        """
        Comprehensive functionality testing
        """
        log.info('test_all')
        assert self.restc is not None
        (status_code, rdata) = self.restc.get(f'http://{host}:{port}/hello')
        self.assertEqual(status_code, 200)
        return
