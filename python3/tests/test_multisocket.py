import socket
from multiprocessing import Process, Queue

from lib.multisocket.multisocket_server import EchoServerManager

DEFAULT_TCP_PORT = 9872
DEFAULT_SERVER = 'localhost'


class TestClient(object):

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

    def assert_recv(self, message):
        assert message in self.message_received_queue.get(timeout=1)

    def close(self):
        self.client_listener_process.terminate()
        self.client_listener_process.join()


def test_basic_echo():
    manager = EchoServerManager(tcp_port=DEFAULT_TCP_PORT)
    manager.start()

    client = TestClient()
    client.send('hello')
    client.assert_recv('hello')

    manager.stop()
