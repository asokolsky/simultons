# How do I programmatically start the FastAPI server?

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
