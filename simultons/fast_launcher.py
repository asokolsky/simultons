"""
FastAPI process launcher
"""

import os
import signal
import subprocess
import time
from pathlib import Path

from strip_ansi import strip_ansi

from . import rest_client, setup_logging, wait_until_reachable

log = setup_logging(__name__)


class FastLauncher:
    """
    FastAPI Service Launcher
    """

    def __init__(self, path: str, port: int) -> None:
        """
        Constructor.
        path - to the python file which has FastAPI global app defined
        """
        self._host = '127.0.0.1'
        self._path = path
        self._port = port
        self._popen: subprocess.Popen | None = None
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

    def launch(self, stdout=subprocess.PIPE, stderr=subprocess.STDOUT) -> int:  # noqa: ANN001
        """
        Start the FastAPI service process.
        To redirect stderr to stdout: stderr=subprocess.STDOUT
        Returns service process pid
        """
        # parent_dir = os.path.abspath(
        #    os.path.dirname(os.path.realpath(__file__)) + '/..')
        parent_dir = Path(__file__).absolute().parents[1]
        command_line = [
            'fastapi',
            'run',
            '--host',
            self._host,
            '--port',
            str(self._port),
            '--workers',
            str(1),
            self._path,
        ]
        log.debug(f'cwd: {parent_dir} command_line: {command_line}')
        self._popen = subprocess.Popen(  # noqa: S603
            command_line,
            cwd=parent_dir,
            stdout=stdout,
            stderr=stderr,  # text=True
        )
        return self._popen.pid

    def wait_until_reachable(self, health_uri: str, timeout: int = 20) -> dict | None:
        """
        Give some room for the process to start.
        Returns a JSON produced by health_uri
        """
        return wait_until_reachable(
            f'http://{self._host}:{self._port}{health_uri}', self._popen, timeout
        )

    def wait_to_die(self, timeout: float = 0.5) -> bool:
        assert self._popen is not None
        if self._popen.returncode is not None:
            log.info(
                f'Pid {self._popen.pid} already terminated with ec: {self._popen.returncode}'
            )
            return True
        #
        # wait for the process to actually terminate
        #
        log.info(f'Waiting for upto {timeout} secs for {self._popen.pid} to die...')
        start = time.time()
        try:
            self._popen.wait(timeout)
            # the process has terminated
            elapsed = time.time() - start
            log.info(
                f'{self._popen.pid} died after {elapsed:.3f} secs, ec: {self._popen.returncode}'
            )
            return True

        except subprocess.TimeoutExpired:
            log.info(
                f'Waiting for {self._popen.pid} to die timed out after {timeout} secs'
            )
        return False

    def shutdown(self, timeout: float = 0.5) -> bool:
        """
        Stop the FastAPI service process
        """
        assert self._popen is not None
        if self._popen.returncode is None:
            try:
                os.kill(self._popen.pid, signal.SIGINT)
            except ProcessLookupError:
                log.info(f'Failed to locate pid {self._popen.pid}')
        else:
            log.info(f'FastAPI is already down, ec: {self._popen.returncode}')
        #
        # wait for the process to actually terminate
        #
        res = self.wait_to_die(timeout)
        #
        # get the child's stdout and stderr
        #
        stdout_value = ''
        stderr_value = ''
        try:
            stdout_value, stderr_value = self._popen.communicate()
        except Exception as err:
            log.info(f'Caught while tying to communicate with {self._popen.pid}: {err}')

        dashes = '==========================='
        output_produced = False
        if stdout_value:
            if isinstance(stdout_value, (bytes, bytearray)):
                stdout_value = stdout_value.decode()
            log.info(f'{dashes} {self._path} {self._popen.pid} stdout {dashes}')
            for line in strip_ansi(stdout_value).splitlines():
                if line:
                    log.info(f'{line}')
            output_produced = True
        if stderr_value:
            if isinstance(stderr_value, (bytes, bytearray)):
                stderr_value = stderr_value.decode()
            log.info(f'{dashes} {self._path} {self._popen.pid} stderr {dashes}')
            for line in strip_ansi(stderr_value).splitlines():
                if line:
                    log.info(f'{line}')
            output_produced = True
        if output_produced:
            log.info(f'{dashes} {self._path} {self._popen.pid} end {dashes}')

        # close the socket
        if self._restc is not None:
            self._restc.close()
            self._restc = None
        return res

    def get_rest_client(self, verbose: bool, dumpHeaders: bool) -> rest_client:
        return rest_client(self._host, self._port, verbose, dumpHeaders)

    def read_stdout(self) -> int | None:
        """
        Capture Python subprocess output in real-time.
        https://lucadrf.dev/blog/python-subprocess-buffers/

        Returns:
         - None if interrupted by KeyboardInterrupt
         - process exit code otherwise

        """
        dashes = '==========================='
        assert self._popen is not None
        print(dashes, self._path, self._popen.pid, 'stdout', dashes)
        ec = self._popen.poll()
        while ec is None:
            try:
                assert self._popen.stdout is not None
                line = self._popen.stdout.readline()
                print(line.rstrip('\r\n '))
            except KeyboardInterrupt:
                break
            ec = self._popen.poll()
        print(dashes, self._path, self._popen.pid, 'end', dashes)
        return ec
