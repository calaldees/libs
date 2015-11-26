from .multisocket_server import ServerManager

import json
from collections import defaultdict

import logging
log = logging.getLogger(__name__)


class SubscriptionEchoServerManager(ServerManager):

    def __init__(self, *args, echo_back_to_source=False, default_subscribe_to_all=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.echo_back_to_source = echo_back_to_source
        self.default_subscribe_to_all = default_subscribe_to_all
        self.subscriptions = defaultdict(set)

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
            except TypeError:
                log.warn('Unable to json decode message: {0}'.format(line))
                continue
            self._process_message(message, source)

    def stop(self):
        self.send(b'server_shutdown')
        super().stop()

    # --------------------------------------------------------------------------

    def _process_message(self, message, source):
        # Handle subscription messages - if present
        if isinstance(message, dict):
            def parse_subscription_set(keys):
                if not keys:
                    return set()
                return {keys} if isinstance(keys, (str, bytes)) else set(keys)
            if 'subscribe' in message:
                self.subscriptions[source] = parse_subscription_set(message.get('subscribe'))
                return

        if not isinstance(message, list):
            message = [message, ]

        # Send message to clients
        for client, client_subscriptions in self.subscriptions.items():
            if not self.echo_back_to_source and client == source:
                continue
            messages_for_this_client = [
                m for m in message
                if (self.default_subscribe_to_all and not client_subscriptions)
                or isinstance(m, dict) and m.get('deviceid') in client_subscriptions
            ]
            if not messages_for_this_client:
                continue
            client.send(
                json.dumps(messages_for_this_client).encode('utf-8') + b'\n',
                source
            )
