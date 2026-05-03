# Simultons Architecture

There is a single [simulation](simulation.md) which provides context for
[simulton](simulton.md)s.

## Simulation

[Simulation](simulation.md) is:

* a process
* a FastAPI service
* a zmq publisher

## Simulton and its Derivatives

[Simulton](simulton.md) is:

* a process (one per simulton instance)
* a FastAPI service
* a zmq subscriber to Simulation publisher
* typically represents a class of objects being simulated

## Major Design Qs

These popped up within hours: How do I programmatically...

* [start the FastAPI server?](fastapi.md)
* [shut the FastAPI server?](fastapi.md)
* [add XXX to the FastAPI event loop?](fastapi.md)

## More readings

https://github.com/encode/uvicorn/issues/761

## How This Works

As an example of how to use this package, consider
[tests/simulation_test.py](../tests/simulation_test.py):

1. [SimulationClient](../simultons/simulation_client.py) is created. This
   loads the settings file, by default [settings.yaml](../settings.yaml).
2. `SimulationClient.set_up()` is called. This identifies the simulation
   implementation, by default [simultons/simulation.py](../simultons/simulation.py),
   and the simulation port, by default `9100` unless a test passes
   `find_free_port()`. It launches the [simulation](simulation.md) and waits for
   the simulation REST API at `/api/v1/simulation` to become available.
3. From now on, `SimulationClient.get_simulation()` and
   `SimulationClient.put_simulation()` issue REST calls to `/api/v1/simulation`.
   `get_simultons()`, `get_simulton()`, and `post_simulton()` issue REST calls to
   `/api/v1/simultons`.
4. To create a new [simulton](simulton.md), such as Clock,
   `SimulationClient.post_simulton()` makes a POST to `/api/v1/simultons`.
   `Simulation.create_simulton()` assigns a free port using `find_free_port()`,
   starts the child process, and waits for its standard `/api/v1/simulton`
   endpoint to become accessible before returning.
