from .multisocket_server import ServerManager

import json
from collections import defaultdict

import logging
log = logging.getLogger(__name__)


class SubscriptionEchoServerManager(ServerManager):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.subscriptions = defaultdict(list)

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

    #---------------------------------------------------------------------------

    def _process_message(self, message, source):
        if 'subscribe' in message:
            self.subscriptions[source] = message.get('subscribe')

        if not isinstance(message, list):
            message = (message, )
        for m in message:
            message_bytes = json.dumps(m).encode('utf-8')
            for client, subscriptions in self.subscriptions.items():
                if client == source:
                    continue
                if not subscriptions or m.get('deviceid') in subscriptions:
                    client.send(message_bytes, source)
