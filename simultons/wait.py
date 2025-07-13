import time
from multiprocessing import Process

import httpx

from . import setup_logging

log = setup_logging(__name__)


def wait_until_reachable(
    url: str, proc: Process | None = None, timeout: int = 20
) -> dict | None:
    """
    Wait upto timeout secs until the url is reachable
    """

    start = time.time()
    time_to_timeout = start + timeout
    log.info(f'wait_until_reachable({url}, {timeout})...')
    while time.time() < time_to_timeout:
        time.sleep(0.5)
        try:
            # are we there yet?
            x = httpx.get(url)
            if x.status_code == 200:
                # YES!
                log.info(
                    f'wait_until_reachable({url}, {timeout}) => {x} after {time.time() - start:.2f} secs'
                )
                res = x.json()
                assert isinstance(res, dict)
                return res

            log.warning(
                f'wait_until_reachable({url}, {timeout}) => {x} after {time.time() - start:.2f} secs'
            )
            return {'resp': x}

        except ValueError as err:  # includes simplejson.decoder.JSONDecodeError
            log.info(f'Caught: {err}')

        except httpx.ConnectError as err:
            log.debug(f'Caught: {err}')

        if proc is not None and not proc.is_alive():
            break

    log.debug(
        f'wait_until_reachable({url}, {timeout}) => None, after {time.time() - start:.2f} secs'
    )
    return None

    # wait until process pid has children
    # while True:
    #    proc = psutil.Process(self._popen.pid)
    #    children = proc.children(recursive=True)
    #    log.info(f'Waiting for children of {self._popen.pid} {children}')
    #    if len(children) > 0:
    #        break
    #    time.sleep(1)
