import json
import socket
from multiprocessing import Process, Queue

DEFAULT_TCP_PORT = 9872
DEFAULT_SERVER = 'localhost'


class SocketClient(object):

    def __init__(self, host=DEFAULT_SERVER, port=DEFAULT_TCP_PORT):
        def connection(sock, message_received_queue):
            while True:
                data_recv = sock.recv(4098)
                if not data_recv:
                    break
                message_received_queue.put(data_recv.decode('utf-8'))
            sock.close()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))
        self.message_received_queue = Queue()
        self.client_listener_process = Process(target=connection, args=(self.sock, self.message_received_queue,))
        self.client_listener_process.daemon = True
        self.client_listener_process.start()

    def send(self, data):
        self.sock.sendall(data.encode('utf-8'))

    @property
    def last_message(self):
        return self.message_received_queue.get(timeout=1)

    def close(self):
        self.client_listener_process.terminate()
        self.client_listener_process.join()


class JSONSocketClient(SocketClient):

    def send(self, data):
        super().send(json.dumps(data))

    @property
    def last_data(self):
        return json.loads(self.last_message)


def test_basic_echo(echo_server):
    client1 = SocketClient()
    client2 = SocketClient()

    MSG1 = 'hello'
    client1.send(MSG1)
    assert client1.last_message == MSG1
    assert client2.last_message == MSG1

    MSG2 = 'test'
    client2.send(MSG2)
    assert client1.last_message == MSG2
    assert client2.last_message == MSG2

    client1.close()
    client2.close()


def test_json(echo_server):
    client1 = JSONSocketClient()
    client1.send({'a': 1})
    assert client1.last_data['a'] == 1
    client1.close()


def test_subscription(subscription_server):
    client1 = SocketClient()
    client2 = SocketClient()

    client1.close()
    client2.close()
