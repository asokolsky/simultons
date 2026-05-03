# simultons — Agent Guide

## What This Project Is

A Python framework for **distributed, multi-process simulation** using FastAPI (REST) and ZeroMQ (pub/sub). The elevator domain is the primary example: buildings, floors, elevator shafts, floor panels, and riders. The project is a personal playground for FastAPI microservices patterns and ZeroMQ messaging — not production software.

Version: `0.2.0` (keep in sync between `pyproject.toml` and `simultons/globals.py`).

## Architecture in One Paragraph

A **Simulation** process (port 9100 by default) is the coordinator: a FastAPI service and a ZeroMQ IPC publisher (`ipc:///tmp/sss`, topic `simulation`). It launches **Simulton** child processes (starting at port 9110, incrementing by 1). Each Simulton is its own FastAPI service that subscribes to the Simulation's ZeroMQ feed. A `SimulationClient` Python object wraps HTTP calls to both layers; a `SimultonClient` wraps calls to an individual simulton. The interactive REPL (`SimultonsShell`, built on `cmd2`) ties it together at the top level.

## Key Files

| Path | Purpose |
|------|---------|
| `simultons/globals.py` | Constants: ZeroMQ spec/topic, API path prefixes, `module_version` |
| `simultons/simulation.py` | `Simulation` class + FastAPI `app`; coordinator process |
| `simultons/simulton.py` | `Simulton` base class; each simulton process inherits from this |
| `simultons/simulton_proxy.py` | `SimultonProxy` — simulation-side handle to a child simulton process |
| `simultons/simulation_client.py` | `SimulationClient` — programmatic client; used by tests and the REPL |
| `simultons/simulton_client.py` | `SimultonClient` — async HTTP client for a single simulton |
| `simultons/schemas.py` | Pydantic models: `SimulationRequest/Response`, `SimultonResponse`, `NewSimultonParams`, `NewClockParams`, `ClockResponse`, `Message`, `Tags`, `SimulationState` |
| `simultons/clock.py` | Example simulton: a collection of named clocks |
| `simultons/clocks_simulton.py` | Clock-specific FastAPI routes |
| `simultons/building/` | Elevator domain: `elevator.py`, `button.py`, `schemas.py` |
| `simultons/__main__.py` | CLI entry point; `SimultonsShell` REPL; `--apply` flag for YAML-driven setup |
| `settings.yaml` | Runtime config (ports, source paths) |
| `logging.yaml` / `logging-min.yaml` | Logging config passed via `--logging-config` |
| `tests/simulation_test.py` | Integration tests; the canonical full-stack usage example |
| `tests/building/elevator_simulton_test.py` | Pattern A (TestClient) canonical example |
| `tests/building/simulton_test.py` | Pattern B (real subprocess) canonical example |

## API Surface

All path constants live in `simultons/globals.py`. Always use the constant, never hardcode the string.

| Constant | Path | Methods | Description |
|----------|------|---------|-------------|
| `api_simulation` | `/api/v1/simulation` | GET, PUT | Simulation state and rate |
| `api_simultons` | `/api/v1/simultons` | GET, POST | List or create simultons |
| _(no constant)_ | `/api/v1/simultons/{id}` | GET | Get one simulton by port |
| `api_simulton` | `/api/v1/simulton` | GET, PUT | Per-simulton self-description (on each simulton's port) |
| `api_clocks` | `/api/v1/clocks` | GET, POST, DELETE `/{id}` | Clock simulton items |
| `api_elevators` | `/api/v1/elevators` | GET, POST | Elevator simulton items |

Interactive docs are served at `http://127.0.0.1:<port>/docs` on every process.

## Toolchain

Managed with **mise** + **uv**. Python 3.13 required.

```sh
mise trust && mise install   # install uv
uv sync --group dev          # install ruff, mypy, and typing deps
mise tests                   # run all unit tests
mise building-tests          # run building/ tests only
mise sim                     # launch the simulation REPL
mise lint                    # ruff check
mise format                  # ruff check --fix + ruff format
mise mypy                    # type-check
mise clean                   # remove .venv, caches, uv.lock
```

Equivalent `make` targets also exist (`make tests`, `make lint`, etc.).

## Running Tests

```sh
uv run -m unittest -v tests/*_test.py tests/building/*_test.py
```

If port 9100 is already in use: `lsof -i :9100` to find and kill the stale process.

### Two test patterns

**Pattern A — `TestClient` (in-process, no real ports):** Use for simulton-level API tests where the full simulation stack is not needed. Fast; no port conflicts. See `tests/building/elevator_simulton_test.py` for the canonical example.

```python
from fastapi.testclient import TestClient
from simultons.building.elevator import app

with TestClient(app) as client:
    response = client.get('/api/v1/elevators/')
    self.assertEqual(response.status_code, 200)
```

**Pattern B — `IsolatedAsyncioTestCase` + `SimultonProxy` or `SimulationClient` (real subprocess, real port):** Use for integration tests that exercise inter-process communication. See `tests/building/simulton_test.py` (single simulton) and `tests/simulation_test.py` (full stack).

```python
class TestFoo(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self._simulton = SimultonProxy('simultons/building/elevator.py', 9100)
        assert self._simulton.launch()
        assert self._simulton.wait_until_reachable()

    async def asyncTearDown(self):
        await self._simulton.shutdown()
```

Always use `assertEqual(response.status_code, N)` — never `assertTrue(response.status_code, N)` (the second arg to `assertTrue` is a message, not an expected value).

## Adding a New Simulton Type

1. Create `simultons/<name>.py` with a `Simulton` subclass and FastAPI routes. The file **must** define a module-level `app` FastAPI instance — this is what the simulation subprocess launcher loads via `NewSimultonParams(src_path=...)`. The subclass must define these class attributes: `title`, `summary`, `description`, `endpoint`, `version`. Override lifecycle hooks as needed: `on_running()`, `on_paused()`, `on_shutting()` (state transitions) and `on_startup()`/`on_shutdown()` (FastAPI lifespan).
2. Add Pydantic schemas to `simultons/schemas.py` (request, response, params).
3. Export new symbols from `simultons/__init__.py` — update `__all__` explicitly; it is not auto-discovered. Do the same for `simultons/building/__init__.py` if adding to the building module.
4. Add API path constant to `simultons/globals.py` if needed.
5. Write tests: use Pattern A (`TestClient`) for simulton-level API tests, Pattern B (`SimultonProxy`) for inter-process tests. See the Running Tests section.
6. Optionally add a YAML definition usable with `simultons --apply <file>`.

## Code Style

- **Formatter/linter:** `ruff` with `line-length = 80`, single-quoted strings.
- **Types:** `mypy` with `warn_return_any = true`. All public functions should be typed.
- Ruff rule set is broad (`select = ["ALL"]`) with a curated ignore list in `pyproject.toml` — don't suppress new categories without justification.
- Logging via `simultons/logging.py`'s `setup_logging(__name__)` — don't use `print()` in library code.

## Ports & Config

Defaults from `settings.yaml`:

| Service | Default Port |
|---------|-------------|
| Simulation | 9100 |
| First simulton | 9110 |
| Subsequent simultons | 9111, 9112, … |

ZeroMQ IPC socket: `ipc:///tmp/sss`

Configurable keys in `settings.yaml`:

| Key | Default | Purpose |
|-----|---------|---------|
| `simulation.source` | `simultons/simulation.py` | Path to the simulation module |
| `simulation.port` | `9100` | Simulation process port |
| `simulation.first_simulton_port` | `9110` | Port assigned to first simulton |
| `simultons.first_port` | `9110` | Same as above (simulton-side view) |

Host is always `127.0.0.1` — remote or `0.0.0.0` binding is not supported.

## Common Gotchas

- `module_version` must be kept in sync between `pyproject.toml` and `simultons/globals.py`.
- `theSimulation` in `simulation.py` is intentionally initialized lazily (not at import time) to avoid creating network resources on `import`.
- The `SimulationClient` context manager (`async with`) handles subprocess lifecycle; always use it or call `set_up()`/`tear_down()` explicitly.
- ZeroMQ sockets must have `LINGER=0` set before closing to avoid hangs on shutdown (already done in `Simulation.on_shutdown`).
- Never import `app` or a concrete simulton class (e.g. `ClocksSimulton`) at the package level in `__init__.py` — doing so instantiates a FastAPI app on import, which opens ports and breaks tests.
