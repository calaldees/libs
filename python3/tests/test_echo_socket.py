import pytest
import socket
import time

from multiprocessing import Process, Queue
from queue import Empty

DEFAULT_TCP_PORT = 9872
DEFAULT_WEBSOCKET_PORT = 9873
DEFAULT_SERVER = 'localhost'


# Server Fixtures --------------------------------------------------------------

@pytest.fixture(scope='module')
def echo_server(request):
    if request.config.getoption("--noserver"):
        return

    from lib.multisocket.multisocket_server import EchoServerManager
    echo_server = EchoServerManager(tcp_port=DEFAULT_TCP_PORT, websocket_port=DEFAULT_WEBSOCKET_PORT)
    echo_server.start()

    def finalizer():
        echo_server.stop()
    request.addfinalizer(finalizer)

    time.sleep(0.01)
    return echo_server



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



def gen_client_fixture(request, client_type=SocketClient):
    client = client_type()
    def finalizer():
        client.close()
    request.addfinalizer(finalizer)
    return client


@pytest.fixture(scope='function')
def client_text1(request):
    return gen_client_fixture(request, SocketClient)
@pytest.fixture(scope='function')
def client_text2(request):
    return gen_client_fixture(request, SocketClient)


@pytest.fixture(scope='function')
def browser_websocket_basic(request, browser, http_server):
    browser.get('http://localhost:8000/websocket_basic.html')
    return browser


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


def test_websocket_echo(echo_server, client_text1, browser_websocket_basic):
    assert browser_websocket_basic.execute_script('return recived_messages') == []

    MSG1 = 'hello websocket'
    client_text1.send(MSG1)

    assert 'hello websocket' in browser_websocket_basic.execute_script('return recived_messages;')
    #assert browser_websocket.execute_script('return 5') == 5
    #assert browser_websocket.find_elements_by_xpath("//*[contains(text(), 'test')]")
