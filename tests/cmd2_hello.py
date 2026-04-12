import asyncio
import concurrent.futures
import sys
import threading
from collections.abc import Coroutine

import cmd2

_event_loop = None
_event_lock = threading.Lock()


def run_async(coro: Coroutine) -> concurrent.futures.Future:
    """Await a coroutine from a synchronous function/method."""

    global _event_loop

    if _event_loop is None:
        with _event_lock:
            if _event_loop is None:
                _event_loop = asyncio.new_event_loop()
                thread = threading.Thread(
                    target=_event_loop.run_forever,
                    name='Async Runner',
                    daemon=True,
                )
                thread.start()

    return asyncio.run_coroutine_threadsafe(coro, _event_loop)


class HelloWorldApp(cmd2.Cmd):
    """
    A simple cmd2 application.
    Demonstrates how to run an async function from a cmd2 command.
    """

    def do_async_wait(self, _: str) -> None:
        """Waits asynchronously."""

        async def async_wait(duration: float) -> float:
            await asyncio.sleep(duration)
            return duration

        waitable = run_async(async_wait(0.1))
        # Wait for coroutine to complete and get its return value:
        res = waitable.result()
        self.poutput(f'Done waiting: {res}')
        return

    def do_hello_world(self, _: str) -> None:
        """Prints a simple greeting."""
        self.poutput('Hello World')


async def main() -> int:
    """
    Having this async ensures presence of the top level event loop.
    """
    c = HelloWorldApp()
    return c.cmdloop()


if __name__ == '__main__':
    sys.exit(asyncio.run(main(), debug=True))
