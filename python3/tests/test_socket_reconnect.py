import pytest
import time

from .test_subscription_socket import subscription_server, client_json1, DEFAULT_WAIT_TIME
from multiprocessing import Queue
import queue



def test_basic_two_way_comms(subscription_server, client_json1, client_reconnect):
    client_json1.send_message({'a': 1})
    assert client_reconnect.pop_message['a'] == 1

    client_reconnect.send_message({'b': 2})
    assert client_json1.pop_payload_item['b'] == 2


def test_burst(subscription_server, client_json1, client_reconnect):
    NUM_MESSAGES = 100
    for i in range(NUM_MESSAGES):
        client_json1.send_message([{'deviceid': 'video', 'message': 'hello9'}, ])

    time.sleep(DEFAULT_WAIT_TIME)

    messages_recieved_count = 0
