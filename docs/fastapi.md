# FastAPI Notes

## Performance and Benchmarking

https://hackeryarn.com/post/async-python-benchmarks/


## How do I programmatically add reading from a 0mq socket to the FastAPI event loop?


https://stackoverflow.com/questions/70872276/fastapi-python-how-to-run-a-thread-in-the-background

1. in the startup event handler add:
```
asyncio.create_task(self.recv_zmq_string())
```

2. define recv_zmq_string

```
    async def recv_zmq_string(self) -> str:
        res = await self._zsocket.recv_string()
        topic, message = res.split()
        assert topic == simulation_ztopic
        # dispatch message
        from pydantic import parse_obj_as
        try:
            self.on_simulation_state_update(
                parse_obj_as(SimulationResponse, json.loads(message)))
        except json.JSONDecodeError as err:
            print('recv_zmq_string caught JSONDecodeError', err)
        except Exception as err:
            print('recv_zmq_string caught Exception', err)

        return message
```


## How do I programmatically start the FastAPI server?

Unfortunately, short answer is "it depends".
Because FastAPI is just an "ASGI app".  If this does not help, I'm with you.


Sources:

* https://github.com/fastapi/fastapi
* https://github.com/fastapi/fastapi-cli
* https://github.com/encode/uvicorn

#### Option 1: launch it using fastapi cli:

```
        '''
        start the FastAPI service process, returns service process pid
        '''
        command_line = [
            'fastapi', 'run', '--host', '127.0.0.1',
            '--port', str(9000), '--workers', str(1), 'app.py'
        ]
        self._popen = subprocess.Popen(
            command_line,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

```
#### Option 2: launch it using uvicorn programmatic API:

uvicorn is used by FastAPI by default anyway...

```
import fastapi
import uvicorn

host = '127.0.0.1'
port = 8000
app = fastapi.FastAPI()


@app.get('/hello')
async def hello():
    return {
        'message': 'hello world'
    }


def launch_uvicorn() -> None:
    '''
    Start FastAPI uvicorn app
    see also:
    https://bugfactory.io/articles/starting-and-stopping-uvicorn-in-the-background/
    '''
    uvicorn.run(app, host=host, port=port, workers=1, log_level='debug')
    return
```

## How do I programmatically shut the FastAPI server?

https://gist.github.com/BnJam/8123540b1716c81922169fa4f7c43cf0

In summary:

1. define an endpoint to shut the server
2. When the endpoint is hit, create a background task to shut the server


```
@app.put(
    '/api/v1/simulation',
    response_model=SimulationResponse,
    status_code=202,
    responses={400: {"model": Message}})
async def put_simulation(req: SimulationRequest, request: Request):
    '''
    Update the simulation state
    '''
    simulation = request.app.state.simulation
    if req.rate is not None:
        simulation.rate = req.rate
    await simulation.setState(req.state)
    if simulation.state == SimulationState.SHUTTING:
        background = BackgroundTask(shut_the_process)
    else:
        background = None
    content = simulation.to_response().model_dump()
    return JSONResponse(status_code=202, content=content, background=background)

async def shut_the_process():
    '''
    This is how we exit FastAPI app
    '''
    pid = os.getpid()
    os.kill(pid, signal.SIGTERM)
    print(f'{pid} shutting down...')
    return
```

## Signals to use

Simultons are terminated using SIGTERM, as the gentlest.  See [termination signal](https://www.gnu.org/software/libc/manual/html_node/Termination-Signals.html) for context.
