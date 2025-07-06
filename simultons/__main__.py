"""
Run the simulation and possibly some simultons
"""

import subprocess

from . import FastLauncher

host = '127.0.0.1'
port = 9000
simulation_uri = '/api/v1/simulation'


def main() -> int:
    """
    Run the simulation
    """
    print('Launching simulation')
    launcher = FastLauncher('simultons/simulation.py', port)
    assert launcher.launch(stderr=subprocess.STDOUT)
    res = launcher.wait_until_reachable(simulation_uri)
    if res:
        launcher.read_stdout()

    launcher.shutdown(timeout=3)
    return 0


if __name__ == '__main__':
    main()
