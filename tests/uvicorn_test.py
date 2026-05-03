"""
Test launching/shutting uvicorn/FastAPI server process
"""

import sys
import unittest
from dataclasses import dataclass
from multiprocessing import get_context
from multiprocessing.connection import Connection
from multiprocessing.process import BaseProcess
from pathlib import Path
from typing import Any

try:
    from fastapi import FastAPI
except ImportError:  # pragma: no cover
    FastAPI = None  # type: ignore[misc, assignment]

import uvicorn

from simultons import (
    SimultonRequest,
    SimultonState,
    api_simulton,
    find_free_port,
    rest_client,
    setup_logging,
    wait_until_reachable,
)

log = setup_logging(__name__)

logging_config = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s <%(process)d:%(processName)s> %(levelname)s %(name)s %(message)s'
        },
        'error': {
            'format': '%(levelname)s <PID %(process)d:%(processName)s> %(name)s.%(funcName)s(): %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
            'stream': 'ext://sys.stdout',
        },
        'error_console': {
            'class': 'logging.StreamHandler',
            'level': 'ERROR',
            'formatter': 'error',
            'stream': 'ext://sys.stderr',
        },
    },
    'root': {'level': 'INFO', 'handlers': ['console'], 'propagate': 'yes'},
    'loggers': {
        'asyncio': {'level': 'DEBUG'},
        'fastapi': {'level': 'DEBUG'},
        'fastapi_cli': {'level': 'DEBUG'},
        'httpcore': {'level': 'INFO'},
        'httpx': {'level': 'WARNING'},
        'simultons': {'level': 'DEBUG'},
        'simultons.wait': {'level': 'INFO'},
        'tests': {'level': 'DEBUG', 'handlers': ['console'], 'propagate': 'no'},
        'uvicorn': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': 'no',
        },
        'werkzeug': {'level': 'DEBUG'},
    },
}


class PipeWriter:
    """
    Facilitates use of Pipe as a stdout/stderr.
    """

    def __init__(self, conn: Connection) -> None:
        self.conn = conn

    def write(self, text: Any) -> None:
        self.conn.send(text)

    def flush(self) -> None:
        # Pipes are generally unbuffered,
        # but implementing flush is good practice.
        pass


@dataclass
class ModuleData:
    module_import_str: str
    extra_sys_path: Path
    module_paths: list[Path]


def get_module_data_from_path(path: Path) -> ModuleData:
    use_path = path.resolve()
    module_path = use_path
    if use_path.is_file() and use_path.stem == '__init__':
        module_path = use_path.parent
    module_paths = [module_path]
    extra_sys_path = module_path.parent
    for parent in module_path.parents:
        init_path = parent / '__init__.py'
        if init_path.is_file():
            module_paths.insert(0, parent)
            extra_sys_path = parent.parent
        else:
            break

    module_str = '.'.join(p.stem for p in module_paths)
    return ModuleData(
        module_import_str=module_str,
        extra_sys_path=extra_sys_path.resolve(),
        module_paths=module_paths,
    )


def launch_uvicorn(conn: Connection, host: str, port: int, path: Path) -> None:
    """
    Start FastAPI uvicorn app.

    https://bugfactory.io/articles/starting-and-stopping-uvicorn-in-the-background/
    https://github.com/fastapi/fastapi-cli/blob/main/src/fastapi_cli/cli.py#L172
    """
    sys.stdout = PipeWriter(conn)
    sys.stderr = PipeWriter(conn)

    log = setup_logging(__name__)
    log.info(f'launch_uvicorn({host}, {port}, {path})')

    assert path.exists()
    mod_data = get_module_data_from_path(path)
    log.debug(f'get_module_data_from_path({path}) => {mod_data}')
    sys.path.insert(0, str(mod_data.extra_sys_path))
    # launch uvicorn app
    uvicorn.run(
        app=f'{mod_data.module_import_str}:app',
        host=host,
        port=port,
        workers=1,
        log_config=logging_config,
    )
    log.info(f'launch_uvicorn({host}, {port}, {path}) => None')
    return


host = '127.0.0.1'


class TestUvicorn(unittest.TestCase):
    """
    Verify launching/shutting a fastapi process
    """

    process: BaseProcess | None = None
    restc = None
    pconn = None

    @classmethod
    def setUpClass(cls) -> None:
        """
        Launch uvicorn/FastAPI process
        """
        log.info('setUpClass')
        port = find_free_port()
        ctxt = get_context('spawn')

        parent_conn, child_conn = ctxt.Pipe()
        cls.pconn = parent_conn
        path: Path = Path('simultons/clocks_simulton.py')
        assert path.exists()
        cls.process = ctxt.Process(
            name=f'{path.stem}-{port}',
            target=launch_uvicorn,
            args=(
                child_conn,
                host,
                port,
                path,
            ),
        )
        assert cls.process is not None
        cls.process.start()
        res = wait_until_reachable(f'http://{host}:{port}{api_simulton}')
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
        params = SimultonRequest(state=SimultonState.SHUTTING)
        (status_code, _) = cls.restc.put(api_simulton, params.model_dump())
        assert status_code == 202

        assert cls.pconn is not None
        while cls.pconn.poll():
            line = cls.pconn.recv()
            if line == '\n':
                continue
            print(f'parent got: {line.strip()}')

        assert cls.process is not None
        cls.process.terminate()

        assert cls.pconn is not None
        while cls.pconn.poll():
            line = cls.pconn.recv()
            if line == '\n':
                continue
            print(f'parent got: {line.strip()}')

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
        (status_code, _) = self.restc.get(api_simulton)
        self.assertEqual(status_code, 200)
        return
