import socket
import json
import datetime
import threading
import time

import logging
log = logging.getLogger(__name__)

# Constants --------------------------------------------------------------------

DEFAULT_HOST = 'localhost'
DEFAULT_PORT = 9872
DEFAULT_RECONNECT_TIMEOUT = datetime.timedelta(seconds=5)


# Null Handler -----------------------------------------------------------------

class DisplayEventHandlerNull(object):

    def event(self, *args, **kwargs):
        log.debug(args)
        pass

    def close(self):
        pass


# Network Display --------------------------------------------------------------

class DisplayEventHandler(object):

    @staticmethod
    def factory(*args, **kwargs):
        try:
            return DisplayEventHandler(*args, **kwargs)
        except socket.error:
            log.warn('Unable to setup TCP network socket {0} {1}'.format(args, kwargs))
            return DisplayEventHandlerNull()

    def __init__(self, host=DEFAULT_HOST, port=DEFAULT_PORT, recive_func=None, reconnect_timeout=DEFAULT_RECONNECT_TIMEOUT):
        self.host = host
        self.port = int(port)
        self.reconnect_timout = reconnect_timeout
        self.socket_connected_attempted_timestamp = None
        self.recive = recive_func
        self.active = True
        self._connect()

    # Connection Management ----------------------------------------------------

    def _connect(self):
        log.debug('Attempting connect TCP network socket {0}:{1}'.format(self.host, self.port))
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))

        if self.recive:
            self.recv_thread = threading.Thread(target=self._recive)
            self.recv_thread.daemon = True
            self.recv_thread.start()

    def _reconnect(self):
        # Don't try to connect if the last connection attempt was very recent
        if self.socket_connected_attempted_timestamp is not None and self.socket_connected_attempted_timestamp > (datetime.datetime.now() - self.reconnect_timout):
            return
        # Ensure existing socket is closed
        self.close()
        # Attempt new connection
        try:
            self._connect()
            return True
        except socket.error:  # ConnectionRefusedError:
            log.debug('Failed to reconnect')
            self.socket_connected_attempted_timestamp = datetime.datetime.now()
            return False

    def close(self):
        try:
            self.socket.close()
        except Exception:
            pass

    # Send ---------------------------------------------------------------------

    def event(self, data):
        try:
            self.socket.sendall((json.dumps(data)+'\n').encode('utf-8'))
        except socket.error:  # BrokenPipeError
            # The data send has failed - for such a transient event we have to just loose the data
            # but we should try to reconnect for the next potential send
            self._reconnect()

    # Recive -------------------------------------------------------------------

    def _recive(self):
        while True:  # self.socket.isConnected
            data = self.socket.recv(4098)
            if not data:
                break
            for line in filter(None, data.decode('utf-8').split('\n')):
                try:
                    line_data = json.loads(line)
                except json.decoder.JSONDecodeError:
                    log.warn('Unable to decode json %s', line)
                    continue
                self.recive(line_data)
        self.close()

        # Attempt reconnect if connection is still active
        while self.active and not self._reconnect():
            time.sleep(self.reconnect_timout.total_seconds())


# Main Demo --------------------------------------------------------------------

if __name__ == "__main__":
    import time
    def recive(data):
        print(data)

    try:
        DisplayEventHandler(recive_func=recive)
        while True:
            time.sleep(1)
    except KeyboardInterrupt as e:
        print("")
