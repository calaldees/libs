# https://gist.github.com/bradmontgomery/2219997
try:
    from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
except ImportError:
    from http.server import HTTPServer, BaseHTTPRequestHandler

import sys
import json
import os
import subprocess

cmd = tuple(sys.argv[1:])

def call(*cmd):
    stdout = open(os.devnull, 'w')
    #with open("./stdout.txt", "w") as stdout:
    subprocess.call(cmd, bufsize=4096, stdout=stdout, stderr=stdout)


class HTTPRequestHandlerShell(BaseHTTPRequestHandler):

    def _set_headers(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()

    def _json(self, data={}):
        self.wfile.write(json.dumps(data).encode("utf8"))

    def do_GET(self):
        self._set_headers()
        print('running CMD')
        call(*cmd)
        print('all done CMD')
        self._json({'status': 'ok'})

    def do_HEAD(self):
        self._set_headers()


def run(request_handler, addr="0.0.0.0", port=80):
    print("Starting httpd server on {addr}:{port}".format(addr=addr, port=port))
    httpd = HTTPServer((addr, port), request_handler)
    httpd.serve_forever()


if __name__ == "__main__":
    run(HTTPRequestHandlerShell)
