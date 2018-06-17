# Dear Python3 ... this is retarded ...
try:
    from .multisocket_server import ServerManager, DEFAULT_TCP_PORT, DEFAULT_WEBSOCKET_PORT
except (SystemError, ModuleNotFoundError):
    from multisocket_server import ServerManager, DEFAULT_TCP_PORT, DEFAULT_WEBSOCKET_PORT


import json
from collections import defaultdict

import logging
log = logging.getLogger(__name__)

__version__ = 0.01


class SubscriptionEchoServerManager(ServerManager):

    def __init__(self, *args, echo_back_to_source=False, auto_subscribe_to_all=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.echo_back_to_source = echo_back_to_source
        self.auto_subscribe_to_all = auto_subscribe_to_all
        self.subscriptions = defaultdict(set)
        self.actions = {
            'subscribe': self._action_subscribe,
            'message': self._action_message,
        }

    def connect(self, client):
        log.info('connection: %s connected' % client.id)
        self.subscriptions[client]

    def disconnect(self, client):
        log.info('connection: %s disconnected' % client.id)
        del self.subscriptions[client]

    def recv(self, data, source=None):
        log.debug('message: {0} - {1}'.format(getattr(source, 'id', None), str(data, 'utf8')))
        for line in filter(None, data.decode('utf-8').split('\n')):
            try:
                message = json.loads(line)
                assert isinstance(message, dict), 'Top level json object must be a dict'
            except Exception:
                log.exception('Unable to json decode message: {0}'.format(line))
                continue

            action = message.get('action')
            if action not in self.actions:
                log.warn('No action handler for {0}'.format(action))
                continue
            self.actions[action](message.get('data'), source)

    def stop(self):
        self.send(b'server_shutdown')
        super().stop()

    # --------------------------------------------------------------------------

    def _action_subscribe(self, data, source):
        """
        Update subscriptions for client
        """
        def parse_subscription_set(keys):
            if not keys:
                return set()
            if isinstance(keys, (str, bytes)):
                return {keys}
            return set(keys)
        self.subscriptions[source] = parse_subscription_set(data)
        return


    def _action_message(self, data, source):
        """
        Send message to subscribed clients
        """
        for client, client_subscriptions in self.subscriptions.items():
            if not self.echo_back_to_source and client == source:
                continue
            messages_for_this_client = [
                m for m in data
                if (self.auto_subscribe_to_all and not client_subscriptions)
                or isinstance(m, dict) and m.get('deviceid') in client_subscriptions
            ]
            if not messages_for_this_client:
                continue
            client.send(
                json.dumps({
                    'action': 'message',
                    'data': messages_for_this_client
                }).encode('utf-8') + b'\n',
                source
            )


# Command line -----------------------------------------------------------------

def get_args():
    import argparse
    parser = argparse.ArgumentParser(
        prog        = "SubscriptionMultiServe",
        description = "Lightweight JSON Subscription server for UDP, TCP and WebSockets",
        epilog      = "@calaldees"
    )
    parser.add_argument('--version', action='version', version="%.2f" % __version__)
    parser.add_argument('-t', '--tcp_port', type=int, help='TCP port', default=DEFAULT_TCP_PORT)
    parser.add_argument('-w', '--websocket_port', type=int, help='WebSocket port', default=DEFAULT_WEBSOCKET_PORT)
    parser.add_argument('--echo_back_to_source', action='store_true', help='All messages are reflected back to the client source', default=False)
    parser.add_argument('--auto_subscribe_to_all', action='store_true', help='If no explicit subscriptions are given then subscribe to all messages', default=True)

    args = parser.parse_args()
    return vars(args)

if __name__ == "__main__":
    options = get_args()
    logging.basicConfig(level=logging.DEBUG)
    manager = SubscriptionEchoServerManager(**options)
    import time
    try:
        manager.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt as e:
        print("")
    manager.stop()
    print("")
