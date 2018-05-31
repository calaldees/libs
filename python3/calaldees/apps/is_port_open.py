#!/usr/bin/python

DESCRIPTION="""
Python util for checking if a port is currently open
"""

import sys
import socket

DEFAULT_HOST = 'localhost'
DEFAULT_PORT = 80


def is_port_open(port=DEFAULT_PORT, host=DEFAULT_HOST, **kwargs):
    return socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect_ex((host, port)) == 0


def get_args():
    import argparse

    parser = argparse.ArgumentParser(
        prog=__name__,
        description=DESCRIPTION,
    )

    parser.add_argument('port', type=int, help='port to check')
    parser.add_argument('--host', action='store', help=' default:({})'.format(DEFAULT_HOST), default=DEFAULT_HOST)
    parser.add_argument('--output_if_open', action='store', help='text to output if port is open', default='')
    parser.add_argument('--output_if_closed', action='store', help='text to output if port is closed', default='')

    args = parser.parse_args()
    return vars(args)


if __name__ == "__main__":
    kwargs = get_args()
    _is_port_open = is_port_open(**kwargs)
    #print('{host}:{port} is {open_closed}'.format(open_closed='open' if _is_port_open else 'closed', **kwargs))
    if _is_port_open and kwargs.get('output_if_open'):
        print(kwargs['output_if_open'])
    if not _is_port_open and kwargs.get('output_if_closed'):
        print(kwargs['output_if_closed'])
    exit(0 if _is_port_open else 1)
