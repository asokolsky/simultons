"""
Run the simulation and possibly some simultons like this:
    python -m simultons --version
"""

import asyncio
import concurrent.futures
import json
import logging
import sys
import threading
from argparse import ArgumentParser, ArgumentTypeError, RawTextHelpFormatter
from pathlib import Path
from typing import Any

import cmd2
from pydantic import ValidationError, validate_call

from . import (
    NewSimultonParams,
    SimulationClient,
    SimulationRequest,
    SimulationResponse,
    SimultonClient,
    SimultonResponse,
    api_simulation,
    api_simulton,
    api_simultons,
    load_yaml,
    module_version,
    # print_logging_tree,
    setup_logging,
)


def eprint(*args: Any) -> None:
    print(*args, file=sys.stderr)


_event_loop = None
_event_lock = threading.Lock()


def run_async(coro) -> concurrent.futures.Future:
    """Await a coroutine from a synchronous function/method."""

    global _event_loop

    if _event_loop is None:
        with _event_lock:
            if _event_loop is None:
                _event_loop = asyncio.new_event_loop()
                thread = threading.Thread(
                    target=_event_loop.run_forever,
                    name='Async Runner',
                    daemon=True,
                )
                thread.start()

    return asyncio.run_coroutine_threadsafe(coro, _event_loop)


class SimultonsShell(cmd2.Cmd):
    def __init__(self, client: SimulationClient) -> None:
        super().__init__(completekey='tab')
        self.prompt = '\n> '
        self._client = client
        self._simulton_client: dict[int, SimultonClient] = {}
        return

    def do_simulation_get(self, _: str) -> None:
        """
        Get the simulation
        """
        simulation = self._client.get_simulation()
        assert isinstance(simulation, SimulationResponse)
        self.poutput(json.dumps(simulation.model_dump(), indent=2))
        return

    def do_simulation_put(self, args: str) -> None:
        """
        Modify the simulation using SimulationRequest
        e.g. {"state": "PAUSED","rate": 1.0}
        """
        try:
            arg = SimulationRequest.model_validate_json(args)
            # self.poutput(json.dumps(arg.model_dump(), indent=2))
            simulation = self._client.put_simulation(arg)
            assert isinstance(simulation, SimulationResponse)
            self.poutput(json.dumps(simulation.model_dump(), indent=2))

        except ValidationError:
            self.perror(f"Error: '{args}' is not a SimulationRequest.")
        return

    def do_simultons_get(self, args: str) -> None:
        """
        Get all or just one simulton
        """
        if not args:
            sims = self._client.get_simultons()
            assert isinstance(sims, dict)
            js = {k: v.model_dump() for k, v in sims.items()}
            self.poutput(json.dumps(js, indent=2))
        else:
            # call a coroutine from this routine
            sim = self._client.get_simulton(args)
            assert isinstance(sim, SimultonResponse)
            self.poutput(json.dumps(sim.model_dump(), indent=2))
        return

    def do_simultons_post(self, args: str) -> None:
        """
        Create a new simulton
        e.g. {"src_path":"simultons/clock.py"}
        """
        try:
            arg = NewSimultonParams.model_validate_json(args)
            # self.poutput(json.dumps(arg.model_dump(), indent=2))
            res = self._client.post_simulton(arg)
            assert isinstance(res, SimultonResponse)
            message = f"""

New simulton API: http://127.0.0.1:{res.port}{api_simulton}
New {res.title} API: http://127.0.0.1:{res.port}{res.endpoint}
Docs: http://127.0.0.1:{res.port}/docs

"""
            self.pfeedback(message)
            self.poutput(json.dumps(res.model_dump(), indent=2))
            # save the SimultonClient for the newly created simulton
            assert isinstance(res.port, int)
            self._simulton_client[res.port] = SimultonClient(res)

        except ValidationError:
            self.perror(f"Error: '{args}' is not a NewSimultonParams.")
        return

    @validate_call
    def do_simulton_get(self, port: int) -> None:
        """
        Retrieve the simulton state using the saved SimultonClient
        e.g. `simulton_get 9110`
        """
        simulton_client = self._simulton_client.get(port, None)
        if simulton_client is None:
            self.perror(f'No simulton on port {port}')
        else:
            waitable = run_async(simulton_client.get_simulton())
            res = waitable.result()
            self.poutput(json.dumps(res.model_dump(), indent=2))
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


async def main() -> int:
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
    ap.add_argument(
        '--apply',
        type=existing_file_path,
        help='Apply the definitions from this YAML file.',
    )
    args = ap.parse_args()
    if args.version:
        print(module_version)
        return 0

    setup_logging(__name__, logging.NOTSET, args.logging_config)
    # print_logging_tree()

    async with SimulationClient(args.settings) as client:
        url = client.url
        intro = f"""
Simulation API: {url}{api_simulation}
Simultons API: {url}{api_simultons}
Docs: {url}/docs"""

        try:
            if args.apply is not None:
                to_apply = load_yaml(args.apply)
                if to_apply is not None:
                    await client.load_simultons(to_apply)

            SimultonsShell(client).cmdloop(intro=intro)
        except KeyboardInterrupt:
            print('exiting')
    return 0


if __name__ == '__main__':
    sys.exit(asyncio.run(main(), debug=True))
