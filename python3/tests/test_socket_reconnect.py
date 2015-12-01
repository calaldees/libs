import pytest

from .test_subscription_socket import subscription_server, client_json1, client_json2
import queue


def test_message(subscription_server, client_json1, client_json2):
    client_json1.send([{'a': 1}])
    with pytest.raises(queue.Empty):
        assert client_json1.last_message
    assert client_json2.last_message[0]['a'] == 1


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
