"""
Run the simulation and possibly some simultons like this:
    python -m simultons --version
"""

import json
import logging
import sys
from argparse import ArgumentParser, ArgumentTypeError, RawTextHelpFormatter
from pathlib import Path
from typing import Any

import cmd2
from pydantic import ValidationError

from . import (
    NewSimultonParams,
    SimulationClient,
    SimulationRequest,
    module_version,
    # print_logging_tree,
    setup_logging,
)


def eprint(*args: Any) -> None:
    print(*args, file=sys.stderr)


class SimultonsShell(cmd2.Cmd):
    def __init__(self, client: SimulationClient) -> None:
        super().__init__(completekey='tab')
        self._client = client
        return

    def do_simulation_get(self, args: str) -> None:
        """
        Get the simulation
        """
        js = self._client.get_simulation()
        self.poutput(json.dumps(js, indent=2))
        return

    def do_simulation_put(self, args: str) -> None:
        """
        Modify the simulation using SimulationRequest
        e.g. {"state": "PAUSED","rate": 1.0}
        """
        try:
            arg = SimulationRequest.model_validate_json(args)
            # self.poutput(json.dumps(arg.model_dump(), indent=2))
            js = self._client.put_simulation(arg)
            self.poutput(json.dumps(js, indent=2))

        except ValidationError:
            self.perror(f"Error: '{args}' is not a SimulationRequest.")
        return

    def do_simultons_get(self, args: str) -> None:
        """
        Get all or just one simulton
        """
        if not args:
            js = self._client.get_simultons()
        else:
            js = self._client.get_simulton(args)
        self.poutput(json.dumps(js, indent=2))
        return

    def do_simultons_post(self, args: str) -> None:
        """
        Create a new simulton
        e.g. {"src_path":"simultons/clock.py"}
        """
        try:
            arg = NewSimultonParams.model_validate_json(args)
            # self.poutput(json.dumps(arg.model_dump(), indent=2))
            js = self._client.post_simulton(arg)
            self.poutput(json.dumps(js, indent=2))

        except ValidationError:
            self.perror(f"Error: '{args}' is not a NewSimultonParams.")
        return


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
    ap.add_argument(
        '--version',
        action='store_true',
        help='Display module version and exit.',
    )
    args = ap.parse_args()
    if args.version:
        print(module_version)
        return 0

    setup_logging(__name__, logging.NOTSET, args.logging_config)
    # print_logging_tree()

    with SimulationClient(args.settings) as client:
        assert client._service is not None
        url = f'http://{client._service.host}:{client._service.port}'
        intro = f"""
Simulation API: {url}/api/v1/simulation
Simultons API: {url}/api/v1/simultons
Docs: {url}/docs"""

        try:
            SimultonsShell(client).cmdloop(intro=intro)
        except KeyboardInterrupt:
            print('exiting')
    return 0


if __name__ == '__main__':
    sys.exit(main())
