"""
Playing with FastAPI, pydantic while simulating stuff
"""

# ruff: noqa: I001
from .logging import setup_logging, print_logging_tree
from .arestc import async_rest_client
from .button import Button, ButtonWithLed, ButtonWithLedPanel
from .restc import rest_client
from .globals import simulation_zspec, simulation_ztopic, module_version
from .schemas import (
    NewClockParams,
    ClockResponse,
    NewElevatorParams,
    ElevatorResponse,
    Message,
    SimulationState,
    SimulationRequest,
    SimulationResponse,
    SimultonState,
    NewSimultonParams,
    SimultonRequest,
    SimultonResponse,
)
from .settings import load_settings
from .wait import wait_until_reachable

# order is important to avoid circular dependency!
from .fast_launcher import FastLauncher
from .simulton import Simulton, shut_the_process
from .elevator import Elevator
from .clock import Clock
from .simulation import Simulation, SimultonProxy, theSimulation
from .simulation_client import SimulationClient

__version__ = module_version

__all__ = [
    # globals.py
    'simulation_ztopic',
    'simulation_zspec',
    # arestc.py
    'async_rest_client',
    # button.py
    'Button',
    'ButtonWithLed',
    'ButtonWithLedPanel',
    # clock.py
    'Clock',
    # fast_launcher.py
    'FastLauncher',
    # elevator_simulton.py
    'app',
    # elevator.py
    'Elevator',
    # restc.py
    'rest_client',
    'wait_until_reachable',
    # simulton.py
    'Simulton',
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
    # simulation.py
    'Simulation',
    'SimulationState',
    'theSimulation',
    'SimultonProxy',
    # settings.py
    'load_settings',
    # simulation_client.py
    'SimulationClient',
    # logging.py
    'setup_logging',
    'print_logging_tree',
    # __init__.py
    #'get_version',
]
