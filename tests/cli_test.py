import subprocess
import tempfile
import time
import unittest
from pathlib import Path

from simultons import ProcessSession, __version__, setup_logging

log = setup_logging(__name__)

timeout = 0.1


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
                f'{popen.pid} terminated after {elapsed:.2f} secs, ec: {popen.returncode}'
            )

        except subprocess.TimeoutExpired:
            elapsed = time.time() - start
            log.info(
                f'Waiting for {popen.pid} timed out after {elapsed:.2f} secs'
            )
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
        ec, out, err = run_simultons_cli(args=['--version'])
        self.assertEqual(ec, 0)
        # print('out:', out)
        # print('err:', err)
        self.assertEqual(out.strip(), __version__)
        self.assertTrue(err, __version__)
        return

    def test_basic(self) -> None:
        cmds = [
            'set debug true',
            'simulation_get',
            'simultons_post  {"src_path":"simultons/clock.py"}',
            #'simultons_post  {"src_path":"simultons/building/elevator.py"}',
            'simultons_get',
            'quit',
        ]
        ec, out, err = run_simultons_cli(cmds=cmds)
        self.assertEqual(ec, 0)
        # print('out:', out)
        # print('err:', err)
        return

    def test_step_by_step(self) -> None:
        """
        Feed the background CLI session one command at a time.
        """

        cmd: list[str] | str = ['.venv/bin/python3', '-m', 'simultons']
        with ProcessSession(cmd) as session:
            cmds = [
                'set debug true',
                'simulation_get',
                'simultons_post  {"src_path":"simultons/clock.py"}',
                'simultons_get',
                'quit',
            ]
            for cmd in cmds:
                log.debug(f'cmd: {cmd}')
                cmd1 = cmd
                while not session.wait(timeout):
                    stdout, stderr = session.consume_outputs(cmd1)
                    # log.debug('out: %s', stdout)
                    # log.debug('err: %s', stderr)
                    if stdout.endswith('\n'):
                        log.debug('Proceeding...')
                        break
                    cmd1 = ''
        return

    def test_script(self) -> None:
        cmds = [
            'set debug true',
            'simulation_get',
            'simultons_post  {"src_path":"simultons/clock.py"}',
            'simultons_get',
            'quit',
        ]
        fname = new_commands_file(cmds)
        log.debug(f'fname: {fname}')
        cmds = ['.venv/bin/python3', '-m', 'simultons']
        with ProcessSession(cmds) as session:
            cmd = f'run_script {fname}'
            log.debug(f'cmd: {cmd}')
            while session.is_alive() and not session.wait(timeout):
                stdout, stderr = session.consume_outputs(cmd)
                # log.debug('out: %s', stdout)
                # log.debug('err: %s', stderr)
                cmd = ''

        log.debug(f'del_commands_file({fname})')
        del_commands_file(fname)
        return
