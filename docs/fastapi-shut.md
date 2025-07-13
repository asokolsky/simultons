# How do I programmatically shut the FastAPI server?

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
async def put_simulation(req: SimulationRequest):
    '''
    Update the simulation state
    '''
    assert theSimulation is not None
    if req.rate is not None:
        theSimulation.rate = req.rate
    # this assignment will result in multiple functions being called
    await theSimulation.setState(req.state)
    if theSimulation.state == SimulationState.SHUTTING:
        background = BackgroundTask(shut_the_process)
    else:
        background = None
    content = SimulationResponse(
        state=theSimulation.state, rate=theSimulation.rate).model_dump()
    return JSONResponse(content=content, background=background)

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
