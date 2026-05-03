# CLI README

## Starting simultons interactive shell

```sh
uv run -m simultons
```

Once the shell starts, the simulation service is launched and the shell prints:
```
Simulation API: http://127.0.0.1:9100/api/v1/simulation
Simultons API: http://127.0.0.1:9100/api/v1/simultons
Docs: http://127.0.0.1:9100/docs
```

The simulation port defaults to `9100` from `settings.yaml`. Simulton child
processes use dynamically assigned free ports. For commands that need a
simulton port, use the numeric port returned by `simultons_post` or use
`latest` for the most recently created simulton.

The shell can also preload simultons from YAML:

```sh
uv run -m simultons --apply tests/simultons.yaml
```

## Simulation commands

### GET

```
(Cmd) simulation_get
16:01:53.595 <97692:MainProcess> DEBUG simultons.restc HTTP GET http://127.0.0.1:9100/api/v1/simulation ...
16:01:53.597 <97712:simulation-9100> INFO uvicorn.access 127.0.0.1:51910 - "GET /api/v1/simulation HTTP/1.1" 200
16:01:53.599 <97692:MainProcess> DEBUG simultons.restc HTTP GET => 200 {'state': 'PAUSED', 'rate': 0.0, 'port': 9100}
{
  "state": "PAUSED",
  "rate": 0.0,
  "port": 9100
}
```

### PUT

```
simulation_put {"state": "RUNNING", "rate": 1.0}
simulation_put {"state": "PAUSED"}
```

## Simulton commands

```
simultons_post {"src_path":"simultons/clocks_simulton.py"}
simulton_get latest
simultons_get latest
simulton_get_items latest
```

## Common shell commands

* quit
* help
* run_script commands.txt
