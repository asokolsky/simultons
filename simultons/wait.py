import time

import httpx


def wait_until_reachable(url: str, timeout: int) -> httpx.Response | None:
    """
    Wait upto timeout secs until the url is reachable
    """
    start = time.time()
    time_to_timeout = start + timeout
    print(f'wait_until_reachable({url}, {timeout})', end='', flush=True)
    while time.time() < time_to_timeout:
        time.sleep(0.1)
        try:
            # are we there yet?
            x = httpx.get(url)
            if x.status_code == 200:
                # YES!
                print(
                    f'\nwait_until_reachable({url}, {timeout}) => {x},'
                    f' after {time.time() - start:.2f} secs'
                )
                return x
        except httpx.ConnectError:
            print('.', end='', flush=True)

    print(f'\nwait_until_reachable({url}, {timeout}) => None')
    return None
