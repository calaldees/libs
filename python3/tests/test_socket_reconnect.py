import pytest

from .test_subscription_socket import subscription_server, client_json1
import queue

from lib.net.network_display_event import DisplayEventHandler


class ReconnectClient(DisplayEventHandler):
    def __init__(self):
        super().__init__(recive_func=self.recive, reconnect_timeout=0.5)
        self.messages = []
    def recive(self, data):
        self.messages.append(data)


@pytest.fixture(scope='function')
def client_tcp_reconnect(request):
    client = ReconnectClient()

    def finalizer():
        client.close()
    request.addfinalizer(finalizer)

    return client


def test_reconnect_client(subscription_server, client_json1, client_tcp_reconnect):
    #messages = []
    #def recive(data):
    #    messages.append(data)
    #client_tcp_reconnect.recive = recive

    client_json1.send([{'a': 1}])

    assert client_tcp_reconnect.messages.pop(0)[0]['a'] == 1


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
