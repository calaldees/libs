import pytest
import time

from .test_subscription_socket import subscription_server, client_json1, DEFAULT_WAIT_TIME
from multiprocessing import Queue
import queue

from lib.net.client_reconnect import SubscriptionClient


class TestJsonSocketReconnect(SubscriptionClient):
    QUEUE_GET_TIMEOUT = 0.1
    RECONNECT_TIMEOUT = 0.1

    def __init__(self):
        self.message_received_queue = Queue()
        super().__init__(reconnect_timeout=TestJsonSocketReconnect.RECONNECT_TIMEOUT)

    def recive_message(self, message):
        self.message_received_queue.put(message)

    @property
    def pop_message(self):
        return self.message_received_queue.get(timeout=self.QUEUE_GET_TIMEOUT)

    def assert_empty(self):
        with pytest.raises(queue.Empty):
            assert not self.pop_message


@pytest.fixture(scope='function')
def client_reconnect(request):
    client = TestJsonSocketReconnect()

    def finalizer():
        client.close()
    request.addfinalizer(finalizer)

    time.sleep(DEFAULT_WAIT_TIME)
    return client


def test_basic_two_way_comms(subscription_server, client_json1, client_reconnect):
    client_json1.send_message({'a': 1})
    assert client_reconnect.pop_message['a'] == 1

    client_reconnect.send_message({'b': 2})
    assert client_json1.pop_payload_item['b'] == 2


def disable_burst(subscription_server, client_json1, client_json2, client_json3):
    NUM_MESSAGES = 100
    for i in range(NUM_MESSAGES):
        client_json1.send([{'deviceid': 'video', 'message': 'hello9'}, ])

    time.sleep(DEFAULT_WAIT_TIME)

    for client in (client_json2, client_json3):
        messages_recieved_count = 0
        try:
            while client.last_message:
                messages_recieved_count += 1
        except queue.Empty:
            assert messages_recieved_count == NUM_MESSAGES
