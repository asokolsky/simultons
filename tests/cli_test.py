import os
import subprocess
import time
import unittest
from collections import deque
from pathlib import Path

from simultons import __version__, setup_logging

log = setup_logging(__name__)


class CliSession:
    """
    Run the cli session.
    """

    def __init__(self) -> None:
        self.popen: subprocess.Popen | None = None
        return

    def __enter__(self) -> 'CliSession':
        """
        Enter the with block, start the CLI session
        """
        log.info('CliSession.__enter__()')

        command_line = ['.venv/bin/python3', '-m', 'simultons']
        parent_dir = Path(__file__).absolute().parents[1]
        self.popen = subprocess.Popen(
            command_line,
            cwd=parent_dir,
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

    def wait(self, timeout: float = 10.0) -> None:
        """
        Wait for the process to terminates
        """

        assert self.popen is not None
        if self.popen.returncode is not None:
            return

        # now wait for the process to complete
        try:
            log.info(f'Waiting for upto {timeout} secs for {self.popen.pid}...')
            start = time.time()
            self.popen.wait(timeout)
            # the process has terminated
            elapsed = time.time() - start
            log.info(
                f'{self.popen.pid} terminated after {elapsed:.3f} secs, ec: {self.popen.returncode}'
            )

        except subprocess.TimeoutExpired:
            elapsed = time.time() - start
            log.info(f'Waiting for {self.popen.pid} timed out after {elapsed} secs')

        return


class TestCLI(unittest.TestCase):
    """
    Verify simultons CLI
    """

    def run_simultons_cli(
        self, args: list[str] = [], timeout: float = 10.0, cmds: list[str] = []
    ) -> tuple[int, str, str]:
        command_line = ['.venv/bin/python3', '-m', 'simultons', *args]
        parent_dir = Path(__file__).absolute().parents[1]
        popen = subprocess.Popen(
            command_line,
            cwd=parent_dir,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        assert popen is not None
        # retrieve stdout and stderr
        stdin_value = '\n'.join(cmds)
        stdout_value = ''
        stderr_value = ''
        try:
            stdout_value, stderr_value = popen.communicate(input=stdin_value)
        except Exception as err:
            log.info(f'Caught while tying to communicate with {popen.pid}: {err}')

        if popen.returncode is None:
            # now wait for the process to complete
            try:
                log.info(f'Waiting for upto {timeout} secs for {popen.pid}...')
                start = time.time()
                popen.wait(timeout)
                # the process has terminated
                elapsed = time.time() - start
                log.info(
                    f'{popen.pid} terminated after {elapsed:.3f} secs, ec: {popen.returncode}'
                )

            except subprocess.TimeoutExpired:
                elapsed = time.time() - start
                log.info(f'Waiting for {popen.pid} timed out after {elapsed} secs')
                return -1, '', ''

        return popen.returncode, stdout_value, stderr_value

    def test_version(self) -> None:
        ec, out, err = self.run_simultons_cli(args=['--version'])
        self.assertEqual(ec, 0)
        # print('out', out)
        # print('err', err)
        self.assertEqual(out.strip(), __version__)
        return

    def test_basic(self) -> None:
        cmds = [
            'simultons_get',
            'simultons_post  {"src_path":"simultons/clock.py"}',
            'simultons_post  {"src_path":"simultons/elevator.py"}',
            'simultons_get',
            'simulation_get',
            'quit',
        ]
        ec, out, err = self.run_simultons_cli(cmds=cmds)
        self.assertEqual(ec, 0)
        print('out', out)
        print('err', err)
        return

    def test_step_by_step(self) -> None:
        """
        Feed the background CLI session one command at a time.
        """

        with CliSession() as session:
            time.sleep(0.5)
            cmd = 'set debug true'
            log.debug(f'cmd: {cmd}')
            while True:
                time.sleep(0.1)
                stdout, stderr = session.consume_outputs(cmd)
                log.debug(f'out: {stdout}')
                log.debug(f'err: {stderr}')
                if 'now: ' in stdout:
                    break
                cmd = ''
            time.sleep(2)

            #cmd = 'simulation_get'
            #stdout, stderr = session.consume_outputs(cmd)
            #log.debug(f'cmd: {cmd}')
            #while True:
            #    time.sleep(0.1)
            #    log.debug(f'out: {stdout}')
            #    log.debug(f'err: {stderr}')
            #    if '}' in stdout:
            #        break
            #    cmd = ''
            #time.sleep(2)

            cmd = 'simultons_post  {"src_path":"simultons/clock.py"}'
            stdout, stderr = session.consume_outputs(cmd)
            log.debug(f'cmd: {cmd}')
            while True:
                time.sleep(0.1)
                log.debug(f'out: {stdout}')
                log.debug(f'err: {stderr}')
                if stdout.endswith('}\n'):
                    break
                cmd = ''
            time.sleep(2)

            cmd = 'quit'
            stdout, stderr = session.consume_outputs(cmd)
            log.debug(f'cmd: {cmd}')
            log.debug(f'out: {stdout}')
            log.debug(f'err: {stderr}')
            session.wait(timeout=2.0)

        return
