"""
Playing with FastAPI, pydantic while simulating stuff
"""

# ruff: noqa: I001
from .logging import setup_logging, print_logging_tree, load_yaml

from .arestc import async_rest_client
from .restc import rest_client
from .globals import (
    simulation_zspec,
    simulation_ztopic,
    module_version,
    api_simulation,
    api_simultons,
    api_simulton,
    api_clocks,
    api_elevators,
)
from .schemas import (
    NewClockParams,
    ClockResponse,
    Message,
    SimulationState,
    SimulationRequest,
    SimulationResponse,
    SimultonState,
    NewSimultonParams,
    SimultonRequest,
    SimultonResponse,
    Tags,
)
from .wait import async_wait_until_reachable, wait_until_reachable
from .process_session import AsyncProcessSession, ProcessSession

# order is important to avoid circular dependency!
from .fast_launcher import FastLauncher
from .simulton import get_random_id, Simulton, shut_the_process
from .simulton_proxy import SimultonProxy
from .simulton_client import SimultonClient
from .simulation import Simulation, theSimulation
from .simulation_client import SimulationClient
from .clock import Clock

__version__ = module_version

__all__ = [
    # globals.py
    'simulation_ztopic',
    'simulation_zspec',
    'api_simulation',
    'api_simultons',
    'api_simulton',
    'api_clocks',
    'api_elevators',
    # arestc.py
    'async_rest_client',
    # clock.py
    'Clock',
    # fast_launcher.py
    'FastLauncher',
    # elevator_simulton.py
    'app',
    # process_session.py
    'ProcessSession',
    'AsyncProcessSession',
    # restc.py
    'rest_client',
    # simulton.py
    'Simulton',
    'get_random_id',
    'shut_the_process',
    # schemas.py
    'NewClockParams',
    'ClockResponse',
    'SimulationState',
    'SimulationRequest',
    'SimulationResponse',
    'NewElevatorParams',
    'SimultonState',
    'NewSimultonParams',
    'SimultonRequest',
    'SimultonResponse',
    'NewElevatorParams',
    'ElevatorResponse',
    'Message',
    'Tags',
    # simulation.py
    'Simulation',
    'SimulationState',
    'theSimulation',
    'SimultonProxy',
    # simulation_client.py
    'SimulationClient',
    # simulton_client.py
    'SimultonClient',
    # logging.py
    'load_yaml',
    'setup_logging',
    'print_logging_tree',
    # __init__.py
    #'get_version',
    # wait.py
    'async_wait_until_reachable',
    'wait_until_reachable',
]
