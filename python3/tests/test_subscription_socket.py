import pytest
import json
import time
import queue
from multiprocessing import Queue


from lib.net.client_reconnect import SubscriptionClient

from .test_echo_socket import gen_client_fixture, DEFAULT_TCP_PORT, DEFAULT_WEBSOCKET_PORT, client_text1

DEFAULT_WAIT_TIME = 0.1


@pytest.fixture(scope='module')
def subscription_server(request):
    if request.config.getoption("--noserver"):
        return

    from lib.multisocket.subscription_server import SubscriptionEchoServerManager
    subscription_server = SubscriptionEchoServerManager(tcp_port=DEFAULT_TCP_PORT, websocket_port=DEFAULT_WEBSOCKET_PORT)
    subscription_server.start()

    def finalizer():
        subscription_server.stop()
    request.addfinalizer(finalizer)

    time.sleep(DEFAULT_WAIT_TIME)  # It may take time to fire up the inital thread
    return subscription_server



class TestSubscriptionClient(SubscriptionClient):
    QUEUE_GET_TIMEOUT = 0.1
    RECONNECT_TIMEOUT = 0.1

    def __init__(self):
        self.message_received_queue = Queue()
        super().__init__(reconnect_timeout=self.RECONNECT_TIMEOUT)

    def receive_message(self, message):
        self.message_received_queue.put(message)

    @property
    def pop_message(self):
        return self.message_received_queue.get(timeout=self.QUEUE_GET_TIMEOUT)

    def pop_message_key(self, key):
        return {m[key] for m in self.pop_messages}

    @property
    def pop_messages(self):
        messages = []
        try:
            while True:
                messages.append(self.pop_message)
        except queue.Empty:
            return messages

    def assert_empty(self):
        with pytest.raises(queue.Empty):
            assert not self.pop_message


@pytest.fixture(scope='function')
def client_json1(request):
    return gen_client_fixture(request, TestSubscriptionClient)
@pytest.fixture(scope='function')
def client_json2(request):
    return gen_client_fixture(request, TestSubscriptionClient)
@pytest.fixture(scope='function')
def client_json3(request):
    return gen_client_fixture(request, TestSubscriptionClient)


@pytest.fixture(scope='function')
def browser_websocket(request, browser, http_server):
    browser.get('http://localhost:8000/websocket.html')
    return browser

# Utils ------------------------------------------------------------------------


# Tests ------------------------------------------------------------------------

def test_message(subscription_server, client_json1, client_json2):
    client_json1.send_message({'a': 1})

    client_json1.assert_empty()
    assert client_json2.pop_message['a'] == 1


def test_multi_message(subscription_server, client_text1, client_json2):
    """
    Some messaged can be sent quickly enough to fill a buffer with multiple messages
    Simulate this by sending a custom json string with new lines
    """
    client_text1.send('''{"action": "message", "data": [{"a": 1}]}\n{"action": "message", "data": [{"b": 2}]}\n''')
    assert client_json2.pop_message['a'] == 1
    assert client_json2.pop_message['b'] == 2


def test_subscribe_simple(subscription_server, client_json1, client_json2):
    client_json2.update_subscriptions('video')
    time.sleep(DEFAULT_WAIT_TIME)

    client_json1.send_message({'a': 1})
    client_json1.assert_empty()
    client_json2.assert_empty()

    client_json1.send_message({'deviceid': 'video', 'item': 'hello'})
    assert client_json2.pop_message['item'] == 'hello'


def test_subscribe_multiple(subscription_server, client_json1, client_json2, client_json3):
    client_json2.update_subscriptions('video')
    client_json3.update_subscriptions('video', 'audio')
    time.sleep(DEFAULT_WAIT_TIME)

    client_json1.send_message({'deviceid': 'video', 'item': 'hello2'})
    assert client_json2.pop_message['item'] == 'hello2'
    assert client_json3.pop_message['item'] == 'hello2'

    client_json1.send_message({'deviceid': 'audio', 'item': 'hello3'})
    client_json2.assert_empty()
    assert client_json3.pop_message['item'] == 'hello3'


def test_multiple_message(subscription_server, client_json1, client_json2, client_json3):
    client_json2.update_subscriptions('video')
    client_json3.update_subscriptions('video', 'audio')
    time.sleep(DEFAULT_WAIT_TIME)

    client_json1.send_message(
        {'deviceid': 'video', 'item': 'hello4'},
        {'deviceid': 'audio', 'item': 'hello5'},
    )

    assert {'hello4'} == client_json2.pop_message_key('item')
    assert {'hello4', 'hello5'} == client_json3.pop_message_key('item')


def test_change_subscription(subscription_server, client_json1, client_json2):
    client_json2.update_subscriptions('video')
    time.sleep(DEFAULT_WAIT_TIME)
    client_json1.send_message({'deviceid': 'video', 'item': 'hello6'}, {})
    assert {'hello6'} == client_json2.pop_message_key('item')

    client_json2.update_subscriptions('audio', 'screen')
    time.sleep(DEFAULT_WAIT_TIME)
    client_json1.send_message({'deviceid': 'video', 'item': 'hello7'}, {})
    client_json2.assert_empty()

    client_json2.update_subscriptions()
    time.sleep(DEFAULT_WAIT_TIME)
    client_json1.send_message({'deviceid': 'video', 'item': 'hello8'})
    assert {'hello8'} == client_json2.pop_message_key('item')


def test_burst(subscription_server, client_json1, client_json2):
    NUM_MESSAGES = 100
    for i in range(NUM_MESSAGES):
        client_json1.send_message({'deviceid': 'video', 'message': 'hello9'})

    time.sleep(DEFAULT_WAIT_TIME)

    assert len(client_json2.pop_messages) == NUM_MESSAGES


def test_websocket(subscription_server, client_json1, browser_websocket):
    client_json1.send_message({'a': 1})
    assert browser_websocket.execute_script('return recived_messages.pop();')['a'] == 1

    browser_websocket.execute_script('''socket.send_message({b:2});''')
    assert client_json1.pop_message['b'] == 2
