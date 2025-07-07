"""
Run the simulation and possibly some simultons
"""

from . import SimulationClient


def main() -> int:
    """
    Run the simulation
    """
    print('Launching simulation')
    client = SimulationClient()
    client.setUp()
    #
    # do something with your life
    #
    client.tearDown()
    return 0


if __name__ == '__main__':
    main()
