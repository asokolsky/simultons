import unittest

from simultons import AsyncProcessSession, ProcessSession, setup_logging

log = setup_logging(__name__)

command = ['.venv/bin/python3', 'tests/cmd2_hello.py']
input_lines = ['hello_world', 'hi', 'quit']


class TestProcessSession(unittest.TestCase):
    """
    Verify ProcessSession functionality
    """

    def test_process_session(self) -> None:
        log.info('test_basic')
        #
        # this will read by line from stdin, replace ` ` with `_`,
        # spit it into stdout
        #
        with ProcessSession(command) as session:
            for line in input_lines:
                line0 = line
                while not session.wait(0.1):
                    stdout, stderr = session.consume_outputs(line0)
                    line0 = ''
                    if stdout or stderr:
                        log.debug(f'stdout: "{stdout.rstrip()}"')
                        log.debug(f'stderr: "{stderr.rstrip()}"')
                        break
        return


class TestAsyncProcessSession(unittest.IsolatedAsyncioTestCase):
    """
    Verify AsyncProcessSession functionality
    """

    async def test_async_process_session(self) -> None:
        log.info('test_basic')
        #
        # this will read by line from stdin, replace ` ` with `_`,
        # spit it into stdout
        #
        async with AsyncProcessSession(command) as session:
            for line in input_lines:
                line0 = line
                while session.is_alive():
                    stdout, stderr = await session.consume_outputs(line0)
                    line0 = ''
                    if stdout or stderr:
                        log.debug(f'stdout: "{stdout.rstrip()}"')
                        log.debug(f'stderr: "{stderr.rstrip()}"')
                        break
        return
