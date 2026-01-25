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

As an example of how to use this package, consider [tests/simulation_test.py](../tests/simulation_test.py):

1. [SimulationClient](../simultons/simulation_client.py) is created.  This:
* loads the settings file, by default [settings.yaml](../settings.yaml).
2. [SimulationClient](../simultons/simulation_client.py) method [set_up](https://github.com/asokolsky/simultons/blob/main/simultons/simulation_client.py#L40) is called.  This:
* identifies (from the settings) the simulation implementation, by default [simultons/simulation.py](https://github.com/asokolsky/simultons/blob/main/simultons/simulation.py), and the port, by default `9100`.
* launches the [simulation](simulation.md) and waits for the simulation REST api at http://127.0.0.1:9100/api/v1/simulation to become available.
3. From now on [SimulationClient](../simultons/simulation_client.py)
* methods `get_simulation` and `put_simulation` can be used to issue corresponding REST calls to the [simulation API](https://github.com/asokolsky/simultons/blob/main/docs/simulation.md#rest-service-apiv1simulation) at `/api/v1/simulation` and
* methods `get_simultons`, `get_simulton` and `post_simulton` can be used to issue corresponding REST calls to the [simultons API](https://github.com/asokolsky/simultons/blob/main/docs/simulation.md#rest-service-apiv1simultons) at `/api/v1/simultons`
4. To create a new [simulton](simulton.md), e.g. Clock, [tests/simulation_test.py](../tests/simulation_test.py):
* makes a call to [SimulationClient](../simultons/simulation_client.py) method `post_simulton`, which, in turn, makes a POST to `/api/v1/simultons`
* waits for the simulton to start and make the standard endpoint `/api/v1/simulton` accessible.
