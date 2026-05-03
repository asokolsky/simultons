# CLI README

## Starting simultons interactive shell

This will create virtual environment and launch the shell:
```sh
uv run -m simultons
```
If the ven is already present:
```sh
uv run -m simultons
```

Once the shell starts, simulation service is launched and
```
Simulation API: http://127.0.0.1:9100/api/v1/simulation
Simultons API: http://127.0.0.1:9100/api/v1/simultons
Docs: http://127.0.0.1:9100/docs
```

## Simulation commands

### GET

```
(Cmd) simulation_get
16:01:53.595 <97692:MainProcess> DEBUG simultons.restc HTTP GET http://127.0.0.1:9100/api/v1/simulation ...
16:01:53.597 <97712:simulation-9100> INFO uvicorn.access 127.0.0.1:51910 - "GET /api/v1/simulation HTTP/1.1" 200
16:01:53.599 <97692:MainProcess> DEBUG simultons.restc HTTP GET => 200 {'state': 'PAUSED', 'rate': 0.0}
{
  "state": "PAUSED",
  "rate": 0.0
}
```

### PUT


## Common shell commands

* quit
* help
* run_script commands.txt

##