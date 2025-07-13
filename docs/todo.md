# TODOs

## TODO

* interactive use via REPL

* use python `with-as` pattern (see [contextlib](https://docs.python.org/3/library/contextlib.html)) to allow for creation of universe filled with simultons;

* full blow simulation of riders/elevators;

* API-based JavaScript GUI for the elevator simulation.

## DONE

* replace fastapi-cli with a direct call to `uvicorn.run`. Benefits:
- get rid of fastapi-cli rich logging and gain control over uvicorn logging;
- speedup? Before : `make tests`: `Ran 19 tests in 51.110s`, produces non-text output.  After: `Ran 19 tests in 30.383s`, clean output.
* use python logging with configuration stored in a dedicated YAML settings file
* introduce application(s) config YAML file, e.g. to set ports
* migrated toolchain to [uv](https://github.com/astral-sh/uv);
* use [httpx](https://www.python-httpx.org/advanced/clients/) instead of
request - especially beneficial because of the asyncio support;
* simultons to subscribe to the [ZeroMQ](https://zeromq.org/) publisher created;
by the simulation - especially beneficial because of suport of one-to-many
communication design pattern;
