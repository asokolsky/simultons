# Copilot / AI Agent Instructions for simultons

Purpose: concise, actionable guidance so an AI coding agent can be productive quickly.

- **Quick commands**
  - Run the CLI: `python -m simultons --settings=settings.yaml` (also available via the `simultons` entry point).
  - Run tests: `make tests` (calls `python -m unittest -v tests/*_test.py`).
  - Lint / format: use `make lint` / `make format` (ruff configured in `pyproject.toml`).

- **Big picture**
  - The package is `simultons/`. It implements a simulation controller plus multiple independent "simulton" processes.
  - A Simulton is a small FastAPI service that exposes a REST API for that simulation entity and subscribes to a central ZMQ topic to receive `SimulationResponse` updates.
  - `SimulationClient`/server components coordinate simulation state; communication is via HTTP for REST APIs and ZMQ for broadcast simulation state updates.

- **Key files to inspect first**
  - `simultons/__main__.py` — CLI shell that interacts with the simulation REST API and can load YAML definitions.
  - `simultons/globals.py` — central constants: `simulation_zspec` (ZMQ endpoint, defaults to `ipc:///tmp/sss`), `simulation_ztopic`, and API path constants (`api_simulation`, `api_simultons`, `api_simulton`, etc.).
  - `simultons/simulton.py` — the `Simulton` base class and expected lifecycle: `on_startup`, `on_shutdown`, `on_put_simulton`, `to_response`, and `create_app`.
  - `simultons/fast_launcher.py` — launches FastAPI processes for individual simultons. It expects a module file that defines a global `app` object.
  - `simultons/schemas.py` — the Pydantic models (SimulationRequest/Response, SimultonRequest/Response, NewSimultonParams). Use these models for request/response shapes.
  - `simultons/restc.py` and `simultons/arestc.py` — synchronous/async REST helpers used to control and query FastAPI services.

- **How simultons are added / expected patterns**
  - A simulton is implemented by deriving from `Simulton` (see `simultons/clock.py` for a concrete example).
  - Required patterns on the derived class:
    - class attributes: `title`, `summary`, `description`, `endpoint`, `version`.
    - implement any instance behavior and rely on `on_startup` to schedule background ZMQ listeners via `recv_zmq_string`.
    - implement `on_put_simulton(self, req, port)` to apply runtime `SimultonRequest` updates and return a FastAPI `JSONResponse`.
    - export a global FastAPI `app` (created with the class lifespan) so `fast_launcher` can start it.

- **Launcher integration details**
  - `fast_launcher.get_module_data_from_path(path)` determines import path and `sys.path` manipulations: the file you pass to `FastLauncher` must resolve to a module exposing `app`.
  - `FastLauncher.launch()` spawns a separate process via multiprocessing `spawn` and runs `uvicorn.run(app=...)` pointing at the module path string.

- **Messaging and APIs**
  - ZMQ: pub/sub uses `simulation_zspec` and `simulation_ztopic`. Simultons subscribe to the topic and react to a `SimulationResponse` JSON payload.
  - REST: endpoints use constants in `globals.py` (e.g., `api_simulton`) and data shapes in `schemas.py`. Use `restc.py` helpers for tests and orchestration code.

- **Developer conventions and gotchas**
  - Tests use Python `unittest` (not pytest). Use `make tests` or `python -m unittest -v tests/*_test.py`.
  - The project targets Python 3.13 (see `pyproject.toml`). Be careful with language features.
  - Formatting and linting use `ruff` rules from `pyproject.toml` (line-length 80, select/ignore lists present).
  - The Makefile uses a small wrapper `uv run` — you can also call Python directly if `uv` is not available.
  - Simultons are long-running FastAPI processes; shutting them down must be cooperative (they react to `SimulationState.SHUTTING` by terminating in some handlers).

- **When changing/adding a simulton**
  - Add the subclass file under `simultons/` or `simultons/building/` and follow `clock.py` as the canonical example.
  - Export a module-level `app` (FastAPI) that uses the class lifespan or instantiates the derived simulton at startup.
  - Ensure `to_response` and `on_put_simulton` map to `SimultonResponse`/`SimultonRequest` shapes from `schemas.py`.
  - Use `fast_launcher` in integration tests to spawn the service and `restc`/`arestc` to exercise endpoints.

- **Limited scope — what not to assume**
  - Do not assume a centralized database; simulation state is in-memory and communicated via ZMQ + HTTP in the process topology.
  - Do not assume `uv` is installed globally; if `make` targets fail, use explicit Python commands above.
