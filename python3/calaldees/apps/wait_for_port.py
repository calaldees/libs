#!/usr/bin/python
import sys
import socket

import time
import datetime

DEFAULT_HOST = 'localhost'
DEFAULT_PORT = 80
DEFAULT_TIMEOUT = 60


def wait_for(
        func_attempt,
        func_is_ok=lambda response: response,
        func_generate_exception=lambda response: Exception('wait_for failed'),
        timeout=5,
        sleep_duration=1,
        ignore_exceptions=False,
        **kwargs
):
    def attempt():
        response = func_attempt()
        return (func_is_ok(response), response)

    response = None
    is_ok = None
    expire_datetime = datetime.datetime.now() + datetime.timedelta(seconds=timeout)
    while datetime.datetime.now() <= expire_datetime:
        if ignore_exceptions:
            try:
                is_ok, response = attempt()
            except Exception:
                pass
        else:
            is_ok, response = attempt()
        if is_ok:
            return response
        time.sleep(float(sleep_duration))
    raise func_generate_exception(response)


def is_port_open(port=DEFAULT_PORT, host=DEFAULT_HOST, **kwargs):
    return socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect_ex((host, port)) == 0


def get_args():
    import argparse

    parser = argparse.ArgumentParser(
        prog=__name__,
        description="""Check/wait for a port to open""",
    )

    parser.add_argument('--port', action='store', type=int, help='port to check', default=DEFAULT_PORT)
    parser.add_argument('--host', action='store', help='host to check', default=DEFAULT_HOST)
    parser.add_argument('--timeout', action='store', type=int, help='timeout in seconds before failure', default=DEFAULT_TIMEOUT)

    args = parser.parse_args()
    return vars(args)


if __name__ == "__main__":
    kwargs = get_args()
    wait_for(
        func_attempt=lambda: is_port_open(**kwargs),
        func_generate_exception=lambda response: Exception('wait_for_port failed {}'.format(kwargs)),
        **kwargs
    )
