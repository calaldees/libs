import pytest
import json
import time

from queue import Empty

from .test_echo_socket import gen_client_fixture, SocketClient, DEFAULT_TCP_PORT, DEFAULT_WEBSOCKET_PORT


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

    return subscription_server


class JSONSocketClient(SocketClient):

    def send(self, data):
        super().send(json.dumps(data))

    @property
    def last_message(self):
        return json.loads(super().last_message)


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


# Tests ------------------------------------------------------------------------

def test_message(subscription_server, client_json1, client_json2):
    client_json1.send([{'a': 1}])
    with pytest.raises(Empty):
        assert client_json1.last_message
    assert client_json2.last_message[0]['a'] == 1


def test_subscribe_simple(subscription_server, client_json1, client_json2):
    client_json2.send({'subscribe': 'video'})
    time.sleep(0.01)

    client_json1.send([{'a': 1}])
    with pytest.raises(Empty):
        assert not client_json1.last_message
    with pytest.raises(Empty):
        assert not client_json2.last_message

    client_json1.send({'deviceid': 'video', 'message': 'hello'})
    assert client_json2.last_message[0]['message'] == 'hello'


def test_subscribe_multiple(subscription_server, client_json1, client_json2, client_json3):
    client_json2.send({'subscribe': 'video'})
    client_json3.send({'subscribe': ['video', 'audio']})
    time.sleep(0.01)

    client_json1.send({'deviceid': 'video', 'message': 'hello2'})
    assert client_json2.last_message[0]['message'] == 'hello2'
    assert client_json3.last_message[0]['message'] == 'hello2'

    client_json1.send([{'deviceid': 'audio', 'message': 'hello3'}])
    with pytest.raises(Empty):
        assert not client_json2.last_message
    assert client_json3.last_message[0]['message'] == 'hello3'


def test_multiple_message(subscription_server, client_json1, client_json2, client_json3):
    client_json2.send({'subscribe': 'video'})
    client_json3.send({'subscribe': ['video', 'audio']})
    time.sleep(0.01)

    client_json1.send([
        {'deviceid': 'video', 'message': 'hello4'},
        {'deviceid': 'audio', 'message': 'hello5'},
    ])

    assert {'hello4'} == {m['message'] for m in client_json2.last_message}
    assert {'hello4', 'hello5'} == {m['message'] for m in client_json3.last_message}


def test_change_subscription(subscription_server, client_json1, client_json2):
    client_json2.send({'subscribe': 'video'})
    time.sleep(0.01)
    client_json1.send([{'deviceid': 'video', 'message': 'hello6'}, ])
    assert {'hello6'} == {m['message'] for m in client_json2.last_message}

    client_json2.send({'subscribe': ['audio', 'screen']})
    time.sleep(0.01)
    client_json1.send([{'deviceid': 'video', 'message': 'hello7'}, ])
    with pytest.raises(Empty):
        assert not client_json2.last_message

    client_json2.send({'subscribe': None})
    time.sleep(0.01)
    client_json1.send([{'deviceid': 'video', 'message': 'hello8'}, ])
    assert {'hello8'} == {m['message'] for m in client_json2.last_message}


def disabled_burst(subscription_server, client_json1, client_json2, client_json3):
    NUM_MESSAGES = 100
    for i in range(NUM_MESSAGES):
        client_json1.send([{'deviceid': 'video', 'message': 'hello9'}, ])

    for client in (client_json2, client_json3):
        messages_recieved_count = 0
        try:
            while client.last_message:
                messages_recieved_count += 1
        except Empty:
            assert messages_recieved_count == NUM_MESSAGES


def test_websocket(subscription_server, client_json1, browser_websocket):
    client_json1.send([{'a': 1}])
    assert browser_websocket.execute_script('return recived_messages.pop();')[0]['a'] == 1

    browser_websocket.execute_script('socket.send([{b:2}]);')
    assert client_json1.last_message[0]['b'] == 2
