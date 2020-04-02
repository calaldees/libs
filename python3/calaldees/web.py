import os
import time
import json
import base64
import urllib.request

import logging
log = logging.getLogger(__name__)

DEFAULT_CACHE_SECONDS = 60 * 60 * 100  # 60seconds * 60mins = 1hour     * 100 = 100hours

def _safe_encode_url(url):
    return base64.urlsafe_b64encode(url.encode('utf8')).decode('utf8')


def get_url(request, cache_path='cache', cache_seconds=DEFAULT_CACHE_SECONDS):
    if isinstance(request, urllib.request.Request):
        url = request.url
    else:
        url = request
    if cache_path:
        cache_filename = os.path.join(cache_path, _safe_encode_url(url))
        if os.path.exists(cache_filename) and (os.stat(cache_filename).st_mtime > time.time() - cache_seconds):
            log.info('Cache: ' + url)
            with open(cache_filename, 'rb') as filehandle:
                return filehandle.read()#.decode('utf8')
    log.info('External: ' + url)
    data = urllib.request.urlopen(request).read()#.decode('utf8')
    if data and cache_path:
        try:
            os.makedirs(cache_path)
        except:
            pass
        with open(cache_filename, 'wb') as filehandle:
            filehandle.write(data) # .encode('utf8')
    return data


def get_json(*args, **kwargs):
    return json.loads(get_url(*args, **kwargs))
