"""
FastAPI process launcher
"""

import contextlib
import os
import signal
import sys
import time
from collections import deque
from dataclasses import dataclass
from multiprocessing import get_context
from multiprocessing.connection import Connection
from pathlib import Path
from typing import Any

import uvicorn

from . import rest_client, wait_until_reachable
from .logging import logging_config, setup_logging

log = setup_logging(__name__)


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


class PipeWriter:
    """
    Facilitates use of Pipe as a stdout/stderr.
    """

    def __init__(self, conn: Connection) -> None:
        self.conn = conn

    def write(self, text: Any) -> None:
        with contextlib.suppress(OSError):
            self.conn.send(text)

    def flush(self) -> None:
        # Pipes are generally unbuffered,
        # but implementing flush is good practice.
        pass


#
# Pass the stdout and stderr of this process to the parent who launched us.
# This may help debugging but slows process shutdown by 10 sec on:
# .venv/bin/python3 -m unittest -k many tests/simulation_test.py
#
redirect_stdout_stderr = False

connection_to_parent: Connection | None = None


def launch_uvicorn(conn: Connection, host: str, port: int, path: Path) -> None:
    """
    Start FastAPI uvicorn app.
    It is executed in the context of the child process.

    https://bugfactory.io/articles/starting-and-stopping-uvicorn-in-the-background/
    https://github.com/fastapi/fastapi-cli/blob/main/src/fastapi_cli/cli.py#L172
    """
    global connection_to_parent
    connection_to_parent = conn
    if redirect_stdout_stderr:
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


dashes = '==========================='


class FastLauncher:
    """
    FastAPI Service Launcher
    """

    def __init__(self, path: str, port: int) -> None:
        """
        Constructor.
        path - to the python file which has FastAPI global app defined
        """
        ctxt = get_context('spawn')

        self._host = '127.0.0.1'
        self._path = Path(path)
        self._port = port
        self._conn, child_conn = ctxt.Pipe()
        self._process = ctxt.Process(
            name=f'{self._path.stem}-{port}',
            target=launch_uvicorn,
            args=(
                child_conn,
                self._host,
                self._port,
                self._path,
            ),
        )
        #
        # control REST client verbosity
        #
        verbose = True
        dumpHeaders = False
        self._restc: rest_client | None = self.get_rest_client(verbose, dumpHeaders)
        return

    @property
    def host(self) -> str:
        """Host accessor"""
        return self._host

    @property
    def port(self) -> int:
        """Port accessor."""
        return self._port

    def launch(self) -> int:
        """
        Start the FastAPI service process.
        Returns service process pid
        """
        # parent_dir = Path(__file__).absolute().parents[1]
        # log.debug(f'cwd: {parent_dir} command_line: {command_line}')
        if not self._path.exists():
            log.error(f'File not found: {self._path}')
            return 0

        self._process.start()
        assert self._process.pid is not None
        return self._process.pid

    def wait_until_reachable(self, health_uri: str, timeout: int = 20) -> dict | None:
        """
        Give some room for the process to start.
        Returns a JSON produced by health_uri
        """
        if self._process.pid == 0:
            log.error('Call launch() before calling wait_until_reachable')
            return None
        if not self._process.is_alive():
            log.error('Process is dead, cant wait')

        return wait_until_reachable(
            f'http://{self._host}:{self._port}{health_uri}', self._process, timeout
        )

    def wait_to_die(self, timeout: float = 0.5) -> bool:
        if not self._process.is_alive():
            log.info(
                f'Pid {self._process.pid} already terminated with ec: {self._process.exitcode}'
            )
            return True
        #
        # wait for the process to actually terminate
        #
        log.info(f'Waiting for upto {timeout} secs for {self._process.pid} to die...')
        start = time.time()
        self._process.join(timeout)
        if self._process.exitcode is not None:
            # the process has terminated
            elapsed = time.time() - start
            log.info(
                f'{self._process.pid} died after {elapsed:.3f} secs, ec: {self._process.exitcode}'
            )
            return True

        log.info(
            f'Waiting for {self._process.pid} to die timed out after {timeout} secs'
        )
        return False

    def get_child_output(self) -> str:
        """
        Get the child's stdout and stderr without blocking
        """
        d: deque = deque()
        try:
            assert self._conn is not None
            while self._conn.poll(0.1):
                d.append(self._conn.recv())
        except EOFError:
            pass
        log.debug(f'get_child_output in {len(d)} parts')
        return ''.join(d)

    def shutdown(self, timeout: float = 0.5) -> bool:
        """
        Stop the FastAPI service process
        """
        log.debug(f'shutdown({timeout})')

        before = self.get_child_output()

        assert self._process is not None
        if self._process.exitcode is None:
            try:
                assert self._process.pid is not None
                log.debug(f'Sending SIGINT to {self._process.pid}')
                os.kill(self._process.pid, signal.SIGINT)
            except ProcessLookupError:
                log.info(f'Failed to locate pid {self._process.pid}')
        else:
            log.debug(f'FastAPI is already down, ec: {self._process.exitcode}')
        #
        # wait for the process to actually terminate
        #
        res = self.wait_to_die(timeout) if self._process.exitcode is None else True
        #
        # get the child's stdout and stderr
        #
        stdouterr_value = before + self.get_child_output()
        #
        # print it to the log
        #
        if stdouterr_value:
            log.info(
                f'{dashes} {self._path} {self._process.pid} stdout/stderr {dashes}'
            )
            for line in stdouterr_value.splitlines():
                if line:
                    log.info(f'{line}')
            log.info(f'{dashes} {self._path} {self._process.pid} end {dashes}')

        # close the socket
        if self._restc is not None:
            self._restc.close()
            self._restc = None
        assert self._conn is not None
        self._conn.close()
        return res

    def get_rest_client(self, verbose: bool, dumpHeaders: bool) -> rest_client:
        return rest_client(self._host, self._port, verbose, dumpHeaders)
