import os
import socket

# keep this in sync with the one in pyproject.toml
module_version = '0.2.0'

api_simulation = '/api/v1/simulation'
api_simultons = '/api/v1/simultons'
api_simulton = '/api/v1/simulton'
api_clocks = '/api/v1/clocks'
api_elevators = '/api/v1/elevators'
simulation_ztopic = 'simulation'


def make_zspec(pid: int | None = None) -> str:
    """Return the ZeroMQ IPC endpoint for the given (or current) process."""
    # simulation_zspec = "tcp://*:5556"
    # simulation_zspec = "ipc:///var/run/sss"
    return f'ipc:///tmp/simultons-{pid or os.getpid()}'


def find_free_port() -> int:
    """Return an ephemeral TCP port that is free at the time of the call."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return int(s.getsockname()[1])
