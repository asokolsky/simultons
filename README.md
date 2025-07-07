# Simultons README

This is a work in progress, not ready for a public review.

I wanted to play with:

* elevator simulation;
* [FastAPI](https://fastapi.tiangolo.com/) for microservices;
* `uv` - based toolchain which seems to offer such performance advantages.

It also appeared that [ZeroMQ](https://zeromq.org/) is a perfect fit to make
things work together.

Simulton is:

* a simulation entity,
* which is a separate process,
* exposing some REST APIs

More [docs](./docs/).

## Unrelated

* [simpy](https://simpy.readthedocs.io/en/latest/) is awesome and is highly
recommended and is NOT used in this project.
* our use of term `simulton` is NOT related to https://ogden.eu/simultons/

## Prerequisites

* python
* [uv](https://github.com/astral-sh/uv)
