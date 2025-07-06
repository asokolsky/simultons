# Simultons Architecture

There is a single [simulation](simulation.md) which provides context for
[simulton](simulton.md)s.

## Simulation

[Simulation](simulation.md) is:

* a process
* a FastAPI service
* a zmq publisher

## Simultons

[Simulton](simulton.md) is:

* a process (one per simulton instance)
* a FastAPI service
* a zmq subscriber to Simulation publisher

## Major Design Qs

These popped up within hours: How do I programmatically...

* [start the FastAPI server?](./fastapi-start.md)
* [shut the FastAPI server?](./fastapi-shut.md)
* [add XXX to the FastAPI event loop?](./fastapi-event-loop.md)

## More readings

https://github.com/encode/uvicorn/issues/761
