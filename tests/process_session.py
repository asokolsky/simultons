"""
Launch a process alongside with the caller,
supply input to that process and read outputs.

Sample usage:

    with ProcessSession(['.venv/bin/python3', '-m', 'simultons']) as session:
        time.sleep(0.5)
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

import os
import subprocess
import time
from collections import deque
from pathlib import Path

from simultons import setup_logging

log = setup_logging(__name__)


class ProcessSession:
    """
    Run the cli session.
    """

    def __init__(
        self,
        command_line: list[str],
    ) -> None:
        self.popen: subprocess.Popen | None = None
        self.command_line = command_line
        return

    def __enter__(self) -> 'ProcessSession':
        """
        Enter the with block, start the CLI session
        """
        log.info('CliSession.__enter__()')
        # parent_dir = Path(__file__).absolute().parents[1]
        self.popen = subprocess.Popen(
            self.command_line,
            # cwd=parent_dir,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        assert self.popen is not None
        assert self.popen.stdout is not None
        assert self.popen.stderr is not None
        os.set_blocking(self.popen.stdout.fileno(), False)
        os.set_blocking(self.popen.stderr.fileno(), False)
        return self

    def __exit__(self, exception_type, exception_value, exception_traceback) -> None:
        """
        Handle the exception(s)
        """
        log.info(
            f'CliSession.__exit__({exception_type}, {exception_value}, {exception_traceback})'
        )
        if self.popen is not None:
            # close the pipes
            if self.popen.stdin is not None:
                self.popen.stdin.close()
            if self.popen.stdout is not None:
                self.popen.stdout.close()
            if self.popen.stderr is not None:
                self.popen.stderr.close()
            # wait for the process to complete
            if not self.wait(1.0):
                self.popen.terminate()
                self.popen = None
        return

    def consume_outputs(self, line: str) -> tuple[str, str]:
        """
        Get all the stdout and stderr that is there
        """

        assert self.popen is not None
        assert self.popen.stdin is not None
        if line:
            if not line.endswith('\n'):
                line += '\n'
            self.popen.stdin.write(line)
            self.popen.stdin.flush()

        # retrieve stdout and stderr

        def consume_output(pipe) -> str:
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
            return True

        # now wait for the process to complete
        log.info(f'Waiting for upto {timeout} secs for {self.popen.pid}...')
        start = time.time()
        try:
            self.popen.wait(timeout)
            # the process has terminated
            elapsed = time.time() - start
            log.info(
                f'{self.popen.pid} terminated after {elapsed:.3f} secs, ec: {self.popen.returncode}'
            )
            return True

        except subprocess.TimeoutExpired:
            elapsed = time.time() - start
            log.info(f'Waiting for {self.popen.pid} timed out after {elapsed:.3f} secs')
        return False
