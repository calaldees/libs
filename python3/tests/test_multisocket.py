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

    def assert_recv(self, message):
        assert message in self.message_received_queue.get(timeout=1)

    def close(self):
        self.client_listener_process.terminate()
        self.client_listener_process.join()


def test_basic_echo(echo_server):
    client1 = SocketClient()
    client2 = SocketClient()

    MSG1 = 'hello'
    client1.send(MSG1)
    client1.assert_recv(MSG1)
    client2.assert_recv(MSG1)

    MSG2 = 'test'
    client2.send(MSG2)
    client1.assert_recv(MSG2)
    client2.assert_recv(MSG2)
