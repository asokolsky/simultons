# Simulation

Simulation is:

* a process
* a FastAPI REST service
* a zmq publisher

## Simulation State

* Init
* Paused
* Running - maybe at a rate != 1
* Shutting

## Simultons

Simulation spawns [simulton](simulton.md)s and eventually shuts them down.

Simulation informs simultons about:

* simulation state, e.g. whether it is paused or is running;
* simulation rate, e.g. 1:1 or 100:1

## REST service /api/v1/simulation

* GET -> [SimulationResponse](../simultons/schemas.py)
* PUT, [SimulationRequest](../simultons/schemas.py) -> [SimulationResponse](../simultons/schemas.py)

## REST service /api/v1/simultons

* GET -> dictionary keyed by simulton port, with [SimultonResponse](../simultons/schemas.py) values
* POST [NewSimultonParams](../simultons/schemas.py) -> [SimultonResponse](../simultons/schemas.py) on a dynamically assigned free port
* GET `/api/v1/simultons/{id}` -> [SimultonResponse](../simultons/schemas.py)
