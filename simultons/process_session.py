"""
Launch a process alongside with the caller,
supply input to that process and read outputs.

Sample usage:

    with ProcessSession(['.venv/bin/python3', '-m', 'simultons']) as session:
        cmd = 'set debug true'
        while not session.wait(0.1):
            stdout, stderr = session.consume_outputs(cmd)
            if 'now: ' in stdout:
                break
            cmd = ''

        cmd = 'quit'
        while not session.wait(0.1):
            stdout, stderr = session.consume_outputs(cmd)
            cmd = ''

"""

import asyncio
import os
import signal
import subprocess
import time
from collections import deque
from contextlib import suppress
from pathlib import Path
from types import TracebackType
from typing import IO, Any, Self

from simultons import setup_logging

log = setup_logging(__name__)


class ProcessSession:
    """
    Run the cli session.
    """

    def __init__(
        self,
        command_line: str | list[str],
        cwd: Path | None = None,
        env: dict | None = None,
    ) -> None:
        self.popen: subprocess.Popen | None = None
        self.command_line = command_line
        # self.cwd = Path(__file__).absolute().parents[1]
        self.cwd = cwd
        self.env = env
        return

    def __enter__(self) -> Self:
        """
        Enter the with block, start the CLI session
        """
        log.debug('ProcessSession.__enter__()')
        self.popen = subprocess.Popen(
            self.command_line,
            cwd=self.cwd,
            env=self.env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            start_new_session=True,
        )
        assert self.popen is not None
        log.debug(f'pid:{self.popen.pid} args:{self.popen.args!r}')
        assert self.popen.stdout is not None
        assert self.popen.stderr is not None
        os.set_blocking(self.popen.stdout.fileno(), False)
        os.set_blocking(self.popen.stderr.fileno(), False)
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
        log.debug(
            f'ProcessSession.__exit__({exception_type}, {exception_value}, {exception_traceback})'
        )
        if self.popen is not None:
            # close the pipes
            if self.popen.stdin is not None:
                self.popen.stdin.close()
            # wait for the process to complete
            if not self.wait(8.0):
                with suppress(ProcessLookupError):
                    os.killpg(self.popen.pid, signal.SIGTERM)
                if not self.wait(2.0):
                    with suppress(ProcessLookupError):
                        os.killpg(self.popen.pid, signal.SIGKILL)
                    self.wait(2.0)
            if self.popen.stdout is not None:
                self.popen.stdout.close()
            if self.popen.stderr is not None:
                self.popen.stderr.close()
            self.popen = None
        return

    def consume_outputs(self, line: str) -> tuple[str, str]:
        """
        Feed line (if non-empty) into the process' stdin,
        get all the stdout and stderr that is there
        """

        assert self.popen is not None
        assert self.popen.stdin is not None
        if line:
            if not line.endswith('\n'):
                line += '\n'
            self.popen.stdin.write(line)
            self.popen.stdin.flush()

        # retrieve stdout and stderr

        def consume_output(pipe: IO[Any] | None) -> str:
            assert pipe is not None
            d: deque = deque()
            while True:
                line = pipe.readline()
                if line:
                    d.append(line)
                else:
                    break
            return ''.join(d)

        stdout = consume_output(self.popen.stdout)
        stderr = consume_output(self.popen.stderr)
        return stdout, stderr

    def wait(self, timeout: float = 10.0) -> bool:
        """
        Wait for the process to terminates.
        Returns True if the process was terminated.
        """

        assert self.popen is not None
        if self.popen.returncode is not None:
            log.debug(f'wait({timeout}) -> True, ec:{self.popen.returncode}')
            return True

        # now wait for the process to complete
        # log.debug(f'Waiting for upto {timeout} secs for {self.popen.pid}...')
        start = time.time()
        try:
            self.popen.wait(timeout)
            # the process has terminated
            elapsed = time.time() - start
            log.debug(
                f'{self.popen.pid} terminated after {elapsed:.2f} secs, ec: {self.popen.returncode}'
            )
            return True

        except subprocess.TimeoutExpired:
            elapsed = time.time() - start
            # log.debug(
            #    f'Waiting for {self.popen.pid} timed out after {elapsed:.2f} secs'
            # )
        return False

    def is_alive(self) -> bool:
        return self.popen is not None and self.popen.returncode is None


class AsyncProcessSession:
    """
    Run the cli session.
    """

    def __init__(self, command_line: list[str]) -> None:
        self.popen: asyncio.subprocess.Process | None = None
        self.command_line = command_line
        return

    async def __aenter__(self) -> Self:
        """
        Enter the with block, start the process session
        """
        log.debug('AsyncProcessSession.__aenter__()')
        self.process = await asyncio.subprocess.create_subprocess_exec(
            self.command_line[0],
            *self.command_line[1:],
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        assert self.process is not None
        assert self.process.stdout is not None
        assert self.process.stderr is not None
        log.debug(f'self.process.pid: {self.process.pid}')
        return self

    async def __aexit__(
        self,
        exception_type: type[BaseException] | None,
        exception_value: BaseException | None,
        exception_traceback: TracebackType | None,
    ) -> None:
        """
        Handle the exception(s) / clean-up
        """
        log.debug(
            f'AsyncProcessSession.__aexit__({exception_type}, {exception_value}, {exception_traceback})'
        )
        if self.process is not None:
            # wait for the process to complete
            await self.process.wait()
        return

    async def consume_outputs(self, line: str) -> tuple[str, str]:
        """
        Feed line (if non-empty) into the process' stdin,
        get all the stdout and stderr that is there
        """

        assert self.process is not None
        assert self.process.stdin is not None
        if line:
            if not line.endswith('\n'):
                line += '\n'
            self.process.stdin.write(line.encode('utf-8'))
            await self.process.stdin.drain()

        # retrieve stdout and stderr
        assert self.process.stdout is not None
        assert self.process.stderr is not None
        stdout_task = asyncio.create_task(self.process.stdout.read(1024))
        stderr_task = asyncio.create_task(self.process.stderr.read(1024))
        # Wait for the first task to complete
        done, pending = await asyncio.wait(
            {stdout_task, stderr_task}, return_when=asyncio.FIRST_COMPLETED
        )
        done_task = done.pop()
        stdout = stderr = ''
        if done_task == stdout_task:
            stdout = stdout_task.result().decode('utf-8')
            stderr_task.cancel()
        else:
            stderr = stderr_task.result().decode('utf-8')
            stdout_task.cancel()

        # log.debug(f'consume_outputs("{line}") -> "{stdout}","{stderr}"')
        return stdout, stderr

    def is_alive(self) -> bool:
        return self.process is not None and self.process.returncode is None
