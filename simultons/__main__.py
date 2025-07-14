"""
Run the simulation and possibly some simultons
"""

import logging
import sys
from argparse import ArgumentParser, ArgumentTypeError, RawTextHelpFormatter
from pathlib import Path

from . import SimulationClient, print_logging_tree, setup_logging


def eprint(*args) -> None:
    print(*args, file=sys.stderr)


def existing_file_path(arg: str) -> str:
    """
    'Type' for argparse - checks that file exists but does not open it.
    """
    path = Path(arg)
    if path.is_file():
        return arg
    # Argparse uses the ArgumentTypeError to give a rejection message like:
    # error: argument input: x does not exist
    raise ArgumentTypeError(f'File {arg} does not exist')


epilog = """Examples:
    python -m simultons --settings=simulation.yaml
"""


def main() -> int:
    """
    Run the simulation
    """
    ap = ArgumentParser(
        prog='simultons',
        description='Run simulation with simultons',
        formatter_class=RawTextHelpFormatter,
        epilog=epilog,
    )
    ap.add_argument(
        '-v',
        '--verbose',
        action='store_true',
        default=False,
        help='Tell more about what is going on',
    )
    ap.add_argument(
        '--settings',
        type=existing_file_path,
        default='settings.yaml',
        help='Settings file in YAML format, defaults to `settings.yaml`',
    )
    ap.add_argument(
        '--logging-config',
        type=existing_file_path,
        default='logging.yaml',
        help='Logging config file in YAML format, defaults to `logging.yaml`',
    )
    args = ap.parse_args()

    log = setup_logging(__name__, logging.NOTSET, args.logging_config)
    print_logging_tree()
    log.debug('Welcome to REPL')

    client = SimulationClient()
    if client.set_up(args.settings):
        #
        # do something with your life
        #
        def get_prompt() -> str:
            url = f'http://{client._service.host}:{client._service.port}'
            return f'API Docs: {url}/docs\nSimulation API endpoint: {url}/api/v1/simulation\nSimultons API endpoint: {url}/api/v1/simultons\n> '

        while True:
            try:
                cmd = input(get_prompt())
                if cmd == '':
                    continue
                if cmd == 'exit':
                    break
                print('Unknown command:', cmd)
                print()
            except EOFError:
                break
    else:
        eprint('Failed to start simulation')
    client.tear_down()
    return 0


if __name__ == '__main__':
    main()
