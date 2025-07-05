# TODOs

* full blow simulation of riders/elevators;
* API-based JavaScript GUI for the elevator simulation.

DONE:

* migrated toolchain to [uv](https://github.com/astral-sh/uv).
* use [httpx](https://www.python-httpx.org/advanced/clients/) instead of
request - especially beneficial because of the asyncio support;
* simultons to subscribe to the [ZeroMQ](https://zeromq.org/) publisher created
by the simulation - especially beneficial because of suport of one-to-many
communication design pattern
