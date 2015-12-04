import socket
import datetime
import time
import json
#from multiprocessing import Process, Queue
import threading

import logging
log = logging.getLogger(__name__)

# Constants --------------------------------------------------------------------

DEFAULT_HOST = 'localhost'
DEFAULT_PORT = 9872
DEFAULT_RECONNECT_TIMEOUT = datetime.timedelta(seconds=5)


# Null Handler -----------------------------------------------------------------

class SocketReconnectNull(object):

    def send(self, *args, **kwargs):
        log.debug(args)
        pass

    def close(self):
        pass


# Network Display --------------------------------------------------------------

class SocketReconnect(object):
    READ_SIZE = 4098

    @staticmethod
    def factory(*args, **kwargs):
        try:
            return SocketReconnect(*args, **kwargs)
        except socket.error:
            log.warn('Unable to setup TCP network socket {0} {1}'.format(args, kwargs))
            return SocketReconnectNull()

    def __init__(self, host=DEFAULT_HOST, port=DEFAULT_PORT, reconnect_timeout=DEFAULT_RECONNECT_TIMEOUT):
        self.host = host
        self.port = int(port)
        self.reconnect_timout = reconnect_timeout if isinstance(reconnect_timeout, datetime.timedelta) else datetime.timedelta(seconds=reconnect_timeout)
        #self.socket_connected_attempted_timestamp = None
        self.active = True
        self.socket = None

        #self.reconnect_supervisor_thread = Process(target=self._reconnect_supervisor)
        #self.reconnect_supervisor_thread.daemon = True
        #self.reconnect_supervisor_thread.start()

        self.connection_thread = threading.Thread(target=self._recive)  #Process(
        self.connection_thread.daemon = True
        self.connection_thread.start()

    def close(self):
        self.active = False
        self.socket.close()

    def _encode(self, data):
        return data

    def _decode(self, data):
        yield data

    def send(self, data):
        try:
            self.socket.sendall(self._encode(data))
        except (socket.error, AttributeError):  # BrokenPipeError
            log.warn('Failed send. Socket not connected: {0}'.format(data))

    def _recive(self):
        while self.active:
            log.info('Attempting socket connection')
            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect((self.host, self.port))
            except Exception as err:
                #"ConnectionRefusedError" in err.reason
                self.socket = None

            try:
                while self.socket and self.active:  # self.socket.isConnected
                    data = self.socket.recv(self.READ_SIZE)
                    if not data:
                        break
                    for d in self._decode(data):
                        self.recive(d)
            except OSError:
                pass

            try:
                self.socket.close()
                self.socket.shutdown(socket.SHUT_RDWR)  # Is this needed?
            except Exception:
                pass
            self.socket = None

            if self.active:
                time.sleep(self.reconnect_timout.total_seconds())

    def recive(self, data):
        """
        To be overridden
        """
        pass


class JsonSocketReconnect(SocketReconnect):
    def _encode(self, data):
        return (json.dumps(data)+'\n').encode('utf-8')

    def _decode(self, data):
        for line in filter(None, data.decode('utf-8').split('\n')):
            try:
                yield json.loads(line)
            except json.decoder.JSONDecodeError:
                log.warn('Unable to decode json %s', line)
                continue


class ExampleSocketReconnect(SocketReconnect):
    def recive(self, data):
        print(data)


# Main Demo --------------------------------------------------------------------

if __name__ == "__main__":

    try:
        client = ExampleSocketReconnect()
        while True:
            time.sleep(1)
    except KeyboardInterrupt as e:
        print("")
