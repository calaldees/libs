import sys
import os
#sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from unittest.mock import Mock

import pytest
import tempfile

from pyramid.testing import DummyRequest
from lib.pyramid_helpers.views.upload import Upload


request_environ = {
    'HTTP_HOST': 'localhost:6543',
        #'wsgi.errors': <_io.TextIOWrapper name='<stderr>' mode='w' encoding='UTF-8'>,
    'HTTP_ACCEPT': '*/*',
        #'wsgi.version': (1, 0),
        #'wsgi.multithread': True,
    'SERVER_SOFTWARE': 'waitress',
    'SERVER_PROTOCOL': 'HTTP/1.1',
        #'wsgi.multiprocess': False,
    'REQUEST_METHOD': 'GET',
    'HTTP_USER_AGENT': 'py.test',
    'PATH_INFO': '/',
    'REMOTE_ADDR': '127.0.0.1',
    'SCRIPT_NAME': '',
    'SERVER_NAME': 'localhost',
    'SERVER_PORT': '6543',
        #'wsgi.input': <_io.BytesIO object at 0x415c64dc>,
        #'wsgi.file_wrapper': <class 'waitress.buffers.ReadOnlyFileBasedBuffer'>,
        #'wsgi.run_once': False,
    'wsgi.url_scheme': 'http',
    'QUERY_STRING': '',
        #'webob._parsed_query_vars': (GET([]), '')}
    'HTTP_CONNECTION': 'keep-alive',
    'HTTP_ACCEPT_ENCODING': 'gzip, deflate',
    'HTTP_ACCEPT': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'HTTP_ACCEPT_LANGUAGE': 'en-gb,en;q=0.5',
}

@pytest.mark.unfinished
def test_upload():
    """
    Reference: Resumable uploads over HTTP. Protocol specification
        http://www.grid.net.ru/nginx/resumable_uploads.en.html

    """
    with tempfile.TemporaryDirectory() as tempdir:
    
        #Example 1: Request from client containing the first segment of the file
        #
        #POST /upload HTTP/1.1
        #Host: example.com
        #Content-Length: 51201
        #Content-Type: application/octet-stream
        #Content-Disposition: attachment; filename="big.TXT"
        #X-Content-Range: bytes 0-51200/511920
        #Session-ID: 1111215056 
        #
        #<bytes 0-51200>
        
        #env = copy.copy(request_environ)
        #env.update({'REQUEST_METHOD': 'POST'})
        request = DummyRequest(headers={
            'Content-Length': 51201,
            'Content-Type': 'application/octet-stream',
            'Content-Disposition': 'attachment; filename="big.TXT"',
            'X-Content-Range': 'bytes 0-51200/511920',
            'Session-ID': 1111215056,
        })  
        request.registry.settings = {'upload.path': tempdir}
        request.body = ('x' * 51201).encode('utf-8')  # fake body content
        response = Upload(request).post()
    
        #Example 2: Response to a request containing first segment of a file
        #
        #HTTP/1.1 201 Created
        #Date: Thu, 02 Sep 2010 12:54:40 GMT
        #Content-Length: 14
        #Connection: close
        #Range: 0-51200/511920
        #
        #0-51200/511920 
        
        assert request.response.status_code == 201
        assert response == '0-51200/511920'
        assert request.response.headers['Range'] == '0-51200/511920'
        
        # Simulate writing the middle of file
        with open(os.path.join(tempdir, '1111215056', 'big.TXT', '51200'), 'wb') as file:
            file.write(('z' * 409608).encode('utf-8'))

        #Example 3: Request from client containing the last segment of the file
        #
        #POST /upload HTTP/1.1
        #Host: example.com
        #Content-Length: 51111
        #Content-Type: application/octet-stream
        #Content-Disposition: attachment; filename="big.TXT"
        #X-Content-Range: bytes 460809-511919/511920
        #Session-ID: 1111215056
        #
        #<bytes 460809-511919>
    
        request = DummyRequest(headers={
            'Content-Length': 51111,
            'Content-Type': 'application/octet-stream',
            'Content-Disposition': 'attachment; filename="big.TXT"',
            'X-Content-Range': 'bytes 460809-511919/511920',
            'Session-ID': 1111215056,
        })
        request.registry.settings = {'upload.path': tempdir}
        request.route_url = Mock(return_value='')
        request.body = ('y' * 51111).encode('utf-8')  # fake body content
        response = Upload(request).post()
        
        #Example 4: Response to a request containing last segment of a file
        #
        #HTTP/1.1 200 OK
        #Date: Thu, 02 Sep 2010 12:54:43 GMT
        #Content-Type: text/html
        #Connection: close
        #Content-Length: 2270
        #
        #<response body>
        
        assert response['files'][0]['name'] == 'big.TXT'
        assert response['files'][0]['size'] == 511920
        with open(os.path.join(tempdir, 'big.TXT'), 'rb') as file:
            data = file.read()
            assert chr(data[0]) == 'x'
            assert chr(data[-1]) == 'y'
