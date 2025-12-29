# Simultons Docs Roadmap

There is a single [simulation](simulation.md) which provides context for [simulton](simulton.md)s.  Read more on:

* [Architecture](architecture.md);
* [TODOs](./todo.md)

## Elevators Terminology

This started as an attempt to build an elevator simulation.

The building has multiple floors and >=1 elevator shaft(s).  Each floor has a
[floor panel](floor-panel.md) for calling an elevator.  Each elevator shaft
has a single [elevator](elevator.md).  There are [rider](rider.md)s who use
elevators by interacting first with a floor panel and then with the elevator
they ride.

## async programming

I found this intriguing: [mikeshardmind/async-utils](https://github.com/mikeshardmind/async-utils).
