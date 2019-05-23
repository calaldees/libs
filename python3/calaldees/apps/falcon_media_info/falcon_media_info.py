import os.path
import json
import datetime

import falcon


# Hachoir ----------------------------------------------------------------------

from hachoir.parser import createParser
from hachoir.metadata import extractMetadata
def hachoir_metadata_dict(filename):
    _metadata = extractMetadata(createParser(filename))
    return {
        key: _metadata.get(key)
        for key in _metadata._Metadata__data.keys()
        if _metadata.has(key)
    }

# JSON

def json_encode_field(obj):
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    if isinstance(obj, datetime.timedelta):
        return obj.total_seconds()
    if isinstance(obj, set):
        return tuple(obj)
    return obj


# Request Handler --------------------------------------------------------------

class MediaInfo():
    def __init__(self, path):
        assert os.path.isdir(path)
        self.path = path

    def on_get(self, request, response):
        response.media = {}
        filename = os.path.join(self.path, request.path.strip('/'))
        if os.path.isdir(filename):
            response.media = os.listdir(filename)
            response.status = falcon.HTTP_200
            return
        if not os.path.isfile(filename):
            response.media = {'error': 'file not found'}
            response.status = falcon.HTTP_400
            return
        try:
            metadata = hachoir_metadata_dict(os.path.join(self.path, filename))
        except Exception as ex:
            response.media = {'error': 'unable to extract metadata', 'reason': str(ex)}
            response.status = falcon.HTTP_500
            return
        metadata = {k: json_encode_field(v) for k, v in metadata.items()}
        response.media.update(metadata)
        response.status = falcon.HTTP_200


# Setup App -------------------------------------------------------------------

def create_wsgi_app(media_path='./', **kwargs):
    media = MediaInfo(media_path)
    app = falcon.API()
    app.add_sink(media.on_get, prefix='/')
    return app


# Commandlin Args -------------------------------------------------------------

def get_args():
    import argparse

    parser = argparse.ArgumentParser(
        prog=__name__,
        description='''
            Provide a URL endpoint to return metadata of media
        ''',
    )

    parser.add_argument('media_path', action='store', default='./', help='')

    parser.add_argument('--host', action='store', default='0.0.0.0', help='')
    parser.add_argument('--port', action='store', default=8000, type=int, help='')

    kwargs = vars(parser.parse_args())
    return kwargs


def init_sigterm_handler():
    """
    Docker Terminate
    https://lemanchet.fr/articles/gracefully-stop-python-docker-container.html
    """
    import signal
    def handle_sigterm(*args):
        raise KeyboardInterrupt()
    signal.signal(signal.SIGTERM, handle_sigterm)


# Main ------------------------------------------------------------------------

if __name__ == '__main__':
    init_sigterm_handler()
    kwargs = get_args()

    from wsgiref import simple_server
    httpd = simple_server.make_server(kwargs['host'], kwargs['port'], create_wsgi_app(**kwargs))
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
