import pytest
import json
import time
import queue

from .test_echo_socket import gen_client_fixture, SocketClient, DEFAULT_TCP_PORT, DEFAULT_WEBSOCKET_PORT, client_text1

DEFAULT_WAIT_TIME = 0.1


@pytest.fixture(scope='module')
def subscription_server(request):
    if request.config.getoption("--noserver"):
        return

    from lib.multisocket.subscription_echo_server import SubscriptionEchoServerManager
    subscription_server = SubscriptionEchoServerManager(tcp_port=DEFAULT_TCP_PORT, websocket_port=DEFAULT_WEBSOCKET_PORT)
    subscription_server.start()

    def finalizer():
        subscription_server.stop()
    request.addfinalizer(finalizer)

    time.sleep(DEFAULT_WAIT_TIME)
    return subscription_server


class JSONSocketClient(SocketClient):

    def send(self, data):
        super().send(json.dumps(data))

    def send_message(self, *data):
        self.send({'action': 'message', 'data': data})

    def send_subcribe(self, *data):
        self.send({'action': 'subscribe', 'data': data})

    @property
    def pop_message(self):
        message = super().pop_message
        try:
            return json.loads(message)
        except json.decoder.JSONDecodeError as e:
            print('unable to decode %s', message)

    @property
    def pop_payload_item(self):
        self.pop_message['message'][0]

    def pop_message_key(self, key):
        return {m[key] for m in self.pop_message['message']}

    def assert_empty(self):
        with pytest.raises(queue.Empty):
            assert not self.pop_message


@pytest.fixture(scope='function')
def client_json1(request):
    return gen_client_fixture(request, JSONSocketClient)
@pytest.fixture(scope='function')
def client_json2(request):
    return gen_client_fixture(request, JSONSocketClient)
@pytest.fixture(scope='function')
def client_json3(request):
    return gen_client_fixture(request, JSONSocketClient)


@pytest.fixture(scope='function')
def browser_websocket(request, browser, http_server):
    browser.get('http://localhost:8000/websocket.html')
    return browser

# Utils ------------------------------------------------------------------------


# Tests ------------------------------------------------------------------------

def test_message(subscription_server, client_json1, client_json2):
    client_json1.send_message({'a': 1})

    client_json1.assert_empty()
    assert client_json2.pop_payload_item['a'] == 1


def test_multi_message(subscription_server, client_text1, client_json2):
    """
    Some messaged can be sent quickly enough to fill a buffer with multiple messages
    Simulate this by sending a custom json string with new lines
    """
    client_text1.send('''{"action": "message", "data": [{"a": 1}]}\n{"action": "message", "data": [{"b": 2}]}\n''')
    assert client_json2.pop_payload_item['a'] == 1
    assert client_json2.pop_payload_item['b'] == 2


def test_subscribe_simple(subscription_server, client_json1, client_json2):
    client_json2.send_subcribe('video')
    time.sleep(DEFAULT_WAIT_TIME)

    client_json1.send_message({'a': 1})
    client_json1.assert_empty()
    client_json2.assert_empty()

    client_json1.send_message({'deviceid': 'video', 'item': 'hello'})
    assert client_json2.pop_payload_item['item'] == 'hello'


def test_subscribe_multiple(subscription_server, client_json1, client_json2, client_json3):
    client_json2.send_subscribe('video')
    client_json3.send_subscribe('video', 'audio')
    time.sleep(DEFAULT_WAIT_TIME)

    client_json1.send_message({'deviceid': 'video', 'item': 'hello2'})
    assert client_json2.pop_payload_item['item'] == 'hello2'
    assert client_json3.pop_payload_item['item'] == 'hello2'

    client_json1.send_message({'deviceid': 'audio', 'item': 'hello3'})
    client_json2.assert_empty()
    assert client_json3.pop_payload_item['item'] == 'hello3'


def test_multiple_message(subscription_server, client_json1, client_json2, client_json3):
    client_json2.send_subscribe('video')
    client_json3.send_subscribe('video', 'audio')
    time.sleep(DEFAULT_WAIT_TIME)

    client_json1.send_message(
        {'deviceid': 'video', 'item': 'hello4'},
        {'deviceid': 'audio', 'item': 'hello5'},
    )

    assert {'hello4'} == client_json2.pop_message_key('item')
    assert {'hello4', 'hello5'} == client_json3.pop_message_key('item')


def test_change_subscription(subscription_server, client_json1, client_json2):
    client_json2.send_subscribe('video')
    time.sleep(DEFAULT_WAIT_TIME)
    client_json1.send_message({'deviceid': 'video', 'item': 'hello6'}, {})
    assert {'hello6'} == client_json2.pop_message_key('item')

    client_json2.send_subscribe('audio', 'screen')
    time.sleep(DEFAULT_WAIT_TIME)
    client_json1.send_message({'deviceid': 'video', 'item': 'hello7'}, {})
    client_json2.assert_empty()

    client_json2.send_subscribe()
    time.sleep(DEFAULT_WAIT_TIME)
    client_json1.send_message({'deviceid': 'video', 'item': 'hello8'})
    assert {'hello8'} == client_json2.pop_message_key('item')


def test_websocket(subscription_server, client_json1, browser_websocket):
    client_json1.send_message({'a': 1})
    assert browser_websocket.execute_script('return recived_messages.pop();')['message'][0]['a'] == 1

    browser_websocket.execute_script('''socket.send({action:'message', data:[{b:2}]});''')
    assert client_json1.pop_payload_item['b'] == 2
