import pytest
import json
import socket
import time
from multiprocessing import Process, Queue
from queue import Empty

DEFAULT_TCP_PORT = 9872
DEFAULT_SERVER = 'localhost'


# Server Fixtures --------------------------------------------------------------

@pytest.fixture(scope='function')
def echo_server(request):
    if request.config.getoption("--noserver"):
        return

    from lib.multisocket.multisocket_server import EchoServerManager
    echo_server = EchoServerManager(tcp_port=9872)
    echo_server.start()

    def finalizer():
        echo_server.stop()
    request.addfinalizer(finalizer)

    return echo_server


@pytest.fixture(scope='session')
def subscription_server(request):
    if request.config.getoption("--noserver"):
        return

    from lib.multisocket.subscription_echo_server import SubscriptionEchoServerManager
    subscription_server = SubscriptionEchoServerManager(tcp_port=9872)
    subscription_server.start()

    def finalizer():
        subscription_server.stop()
    request.addfinalizer(finalizer)

    return subscription_server


# Client Fixtures --------------------------------------------------------------

class SocketClient(object):
    QUEUE_GET_TIMEOUT = 0.1

    def __init__(self, host=DEFAULT_SERVER, port=DEFAULT_TCP_PORT):
        self.running = True
        def connection(sock, message_received_queue):
            while self.running:
                data_recv = sock.recv(4098)
                if not data_recv:
                    break
                message_received_queue.put(data_recv.decode('utf-8'))

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))
        self.message_received_queue = Queue()
        self.client_listener_process = Process(target=connection, args=(self.sock, self.message_received_queue,))
        self.client_listener_process.daemon = True
        self.client_listener_process.start()

    def send(self, data):
        self.sock.sendall(data.encode('utf-8')+b'\n')

    @property
    def last_message(self):
        return self.message_received_queue.get(timeout=self.QUEUE_GET_TIMEOUT).strip()

    def close(self):
        self.running = False
        self.sock.shutdown(socket.SHUT_RDWR)
        #self.client_listener_process.terminate()
        self.client_listener_process.join()


class JSONSocketClient(SocketClient):

    def send(self, data):
        super().send(json.dumps(data))

    @property
    def last_message(self):
        return json.loads(super().last_message)


def _gen_client_fixture(request, client_type=SocketClient):
    client = client_type()
    def finalizer():
        client.close();
    request.addfinalizer(finalizer)
    return client


@pytest.fixture(scope='function')
def client_text1(request):
    return _gen_client_fixture(request, SocketClient)
@pytest.fixture(scope='function')
def client_text2(request):
    return _gen_client_fixture(request, SocketClient)
@pytest.fixture(scope='function')
def client_json1(request):
    return _gen_client_fixture(request, JSONSocketClient)
@pytest.fixture(scope='function')
def client_json2(request):
    return _gen_client_fixture(request, JSONSocketClient)
@pytest.fixture(scope='function')
def client_json3(request):
    return _gen_client_fixture(request, JSONSocketClient)


# Tests ------------------------------------------------------------------------

def test_basic_echo(echo_server, client_text1, client_text2):

    MSG1 = 'hello'
    client_text1.send(MSG1)
    assert client_text1.last_message == MSG1
    assert client_text2.last_message == MSG1

    MSG2 = 'test'
    client_text2.send(MSG2)
    assert client_text1.last_message == MSG2
    assert client_text2.last_message == MSG2


def test_subscription_message(subscription_server, client_json1, client_json2):
    client_json1.send([{'a': 1}])
    with pytest.raises(Empty):
        assert client_json1.last_message
    assert client_json2.last_message[0]['a'] == 1


def test_subscription_subscribe_simple(subscription_server, client_json1, client_json2):
    client_json2.send({'subscribe': 'video'})
    time.sleep(0.01)

    client_json1.send([{'a': 1}])
    with pytest.raises(Empty):
        assert not client_json1.last_message
    with pytest.raises(Empty):
        assert not client_json2.last_message

    client_json1.send({'deviceid': 'video', 'message': 'hello'})
    assert client_json2.last_message[0]['message'] == 'hello'


def test_subscription_subscribe_multiple(subscription_server, client_json1, client_json2, client_json3):
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


def test_subscription_multiple_message(subscription_server, client_json1, client_json2, client_json3):
    client_json2.send({'subscribe': 'video'})
    client_json3.send({'subscribe': ['video', 'audio']})
    time.sleep(0.01)

    client_json1.send([
        {'deviceid': 'video', 'message': 'hello4'},
        {'deviceid': 'audio', 'message': 'hello5'},
    ])

    assert {'hello4'} == {m['message'] for m in client_json2.last_message}
    assert {'hello4', 'hello5'} == {m['message'] for m in client_json3.last_message}


def test_subscription_change_subscription(subscription_server, client_json1, client_json2):
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
