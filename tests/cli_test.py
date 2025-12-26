import subprocess
import tempfile
import time
import unittest
from pathlib import Path

from simultons import ProcessSession, __version__, setup_logging

log = setup_logging(__name__)


def run_simultons_cli(
    args: list[str] = [], timeout: float = 10.0, cmds: list[str] = []
) -> tuple[int, str, str]:
    """
    Returns tuple: ec, stdout_str, stderr_str
    """
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


def new_commands_file(cmds: list[str]) -> str:
    """
    Create new temp text file, and fill it with the provided commands.
    Returns path.
    """
    with tempfile.NamedTemporaryFile(
        mode='w+t', delete=False, encoding='utf-8', suffix='.txt'
    ) as file:
        file.write('\n'.join(cmds) + '\n')
        return file.name
    return ''


def del_commands_file(name: str) -> None:
    Path(name).unlink()
    return


class TestCLI(unittest.TestCase):
    """
    Verify simultons CLI
    """

    def test_version(self) -> None:
        ec, out, _ = run_simultons_cli(args=['--version'])
        self.assertEqual(ec, 0)
        # print('out', out)
        # print('err', err)
        self.assertEqual(out.strip(), __version__)
        return

    def test_basic(self) -> None:
        cmds = [
            'simultons_get',
            #'simultons_post  {"src_path":"simultons/clock.py"}',
            #'simultons_post  {"src_path":"simultons/building/elevator.py"}',
            #'simultons_get',
            #'simulation_get',
            'quit',
        ]
        ec, out, err = run_simultons_cli(cmds=cmds)
        self.assertEqual(ec, 0)
        print('out', out)
        print('err', err)
        return

    def test_step_by_step(self) -> None:
        """
        Feed the background CLI session one command at a time.
        """

        cmd: list[str] | str = ['.venv/bin/python3', '-m', 'simultons']
        with ProcessSession(cmd) as session:
            cmd = 'set debug true'
            log.debug(f'cmd: {cmd}')
            while not session.wait(0.1):
                stdout, stderr = session.consume_outputs(cmd)
                if stdout:
                    log.debug(f'out: {stdout}')
                if stderr:
                    log.debug(f'err: {stderr}')
                if 'now: ' in stdout:
                    log.debug('Proceeding...')
                    break
                cmd = ''

            # cmd = 'simulation_get'
            # stdout, stderr = session.consume_outputs(cmd)
            # log.debug(f'cmd: {cmd}')
            # while not session.wait(0.1):
            #    log.debug(f'out: {stdout}')
            #    log.debug(f'err: {stderr}')
            #    if '}' in stdout:
            #        break
            #    cmd = ''
            # time.sleep(2)

            # cmd = 'simultons_post  {"src_path":"simultons/clock.py"}'
            # stdout, stderr = session.consume_outputs(cmd)
            # log.debug(f'cmd: {cmd}')
            # while not session.wait(0.1):
            #    log.debug(f'out: {stdout}')
            #    log.debug(f'err: {stderr}')
            #    if stdout.endswith('}\n'):
            #        break
            #    cmd = ''
            # time.sleep(2)

            cmd = 'quit'
            log.debug(f'cmd: {cmd}')
            while not session.wait(0.1):
                stdout, stderr = session.consume_outputs(cmd)
                if stdout:
                    log.debug(f'out: {stdout}')
                if stderr:
                    log.debug(f'err: {stderr}')
                cmd = ''

        return

    def test_script(self) -> None:
        fname = new_commands_file(['set debug true', 'simulation_get', 'quit'])
        log.debug(f'fname: {fname}')
        cmds = ['.venv/bin/python3', '-m', 'simultons']
        with ProcessSession(cmds) as session:
            cmd = f'run_script {fname}'
            log.debug(f'cmd: {cmd}')
            while session.is_alive() and not session.wait(0.1):
                stdout, stderr = session.consume_outputs(cmd)
                if stdout:
                    log.debug(f'out: {stdout}')
                if stderr:
                    log.debug(f'err: {stderr}')
                cmd = ''

        log.debug(f'del_commands_file({fname})')
        del_commands_file(fname)
        return
