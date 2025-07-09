"""
Run the simulation and possibly some simultons
"""

from . import SimulationClient, setup_logging

log = setup_logging(__name__)


def main() -> int:
    """
    Run the simulation
    """
    log.debug('Launching simulation')
    client = SimulationClient()
    client.set_up()
    #
    # do something with your life
    #
    client.tear_down()
    return 0


if __name__ == '__main__':
    main()
