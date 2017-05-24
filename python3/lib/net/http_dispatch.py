import socket
import re
from itertools import chain

import logging
log = logging.getLogger(__name__)


def http_dispatch(func_dispatch, request_regexs=(), port=23487):
    """
    A super simple single thread tiny http framework

    func_dispatch(request_dict, response_dict):
        return response_dict

    References
     - http://danielhnyk.cz/simple-server-client-aplication-python-3/
     - https://www.tutorialspoint.com/http/http_requests.htm
     - https://www.tutorialspoint.com/http/http_responses.htm
     - https://docs.python.org/3/howto/sockets.html
     - https://ruturajv.wordpress.com/2005/12/27/conditional-get-request/
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as soc:
        soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        soc.bind(('', port))
        soc.listen(1)
        while True:
            log.debug(f'HTTP Dispatch: Waiting on {port}')
            connection, ip_address = soc.accept()
            log.debug(f'Client Connected: {ip_address}')
            # TODO: Thread the handling of each request?
            with connection:
                data = connection.recv(1024)  # TODO: Loop over recv? We may have larger requests
                if not data:
                    break

                request = data.decode('utf8')  # TODO: Separate out head and body and decode separately (to allow binary bodys if required)
                request_dict = dict(
                    ((match.group(1), match.group(2)) for match in re.finditer(r'(.*?)\: (.*)', request)),
                    **re.match(r'(?P<method>.*?) (?P<path>.*) HTTP/1', request).groupdict(),
                    **{
                        'ip': ip_address
                    }
                )

                # Create stub HTTP response headers
                response_dict = {
                    'Server': 'http_dispatch 0.0.0',
                    'Content-Length': None,
                    'Content-Type': 'text/plain',
                    'Connection': 'Closed',
                    '_status': '200 OK',
                    '_body': b'',
                }

                # Perform dispatch
                response_dict = func_dispatch(request_dict, response_dict)

                if not response_dict['Content-Length']:
                    response_dict['Content-Length'] = len(response_dict['_body'])

                # Construct Response
                connection.sendall('\n'.join(chain(
                    ('HTTP/1.1 {_status}', ),
                    tuple(f'{k}: {v}' for k, v in response_dict.items() if not k.startswith('_')),
                    ('\n', ),
                )).encode('utf8'))
                # Send body (if required)
                if request_dict['method'] != 'HEAD':
                    connection.sendall(response_dict['_body'])


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    def example_func_dispatch(request_dict, response_dict):
        print(request_dict)
        response_dict['_body'] = b'Text is good. Dont ask me about ' + request_dict['path'].encode('utf8')
        return response_dict

    http_dispatch(example_func_dispatch)
