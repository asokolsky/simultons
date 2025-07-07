import time
from subprocess import Popen, TimeoutExpired

import httpx


def wait_until_reachable(
    url: str, popen: Popen | None = None, timeout: int = 20
) -> dict | None:
    """
    Wait upto timeout secs until the url is reachable
    """

    def wait(secs: int) -> bool:
        if popen is None:
            time.sleep(secs)
        else:
            try:
                popen.wait(secs)
                return False
            except TimeoutExpired:
                pass
        return True

    start = time.time()
    time_to_timeout = start + timeout
    print(f'::wait_until_reachable({url}, {timeout})', end='', flush=True)
    while time.time() < time_to_timeout:
        if not wait(1):
            # if we are here, this means the process has terminated
            print(
                # f'wait_until_reachable({url}, {timeout}) => None,'
                f' => None after {time.time() - start:.2f} secs, process terminated'
            )
            return None
        print('.', end='', flush=True)
        try:
            # are we there yet?
            x = httpx.get(url)
            if x.status_code == 200:
                # YES!
                print()
                print(
                    f'::wait_until_reachable({url}, {timeout}) => {x},'
                    f' after {time.time() - start:.2f} secs'
                )
                res = x.json()
                assert isinstance(res, dict)
                return res

            assert False, 'What do we do now?'

        except ValueError as err:  # includes simplejson.decoder.JSONDecodeError
            print('Caught:', err)

        except httpx.ConnectError:
            pass

    print()
    print(f'::wait_until_reachable({url}, {timeout}) => None')
    return None

    # wait until process pid has children
    # while True:
    #    proc = psutil.Process(self._popen.pid)
    #    children = proc.children(recursive=True)
    #    print('Waiting for children of', self._popen.pid, children)
    #    if len(children) > 0:
    #        break
    #    time.sleep(1)
