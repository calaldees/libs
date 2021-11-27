import os
import urllib.request
import re
import datetime
import time
import hashlib

import logging
log = logging.getLogger(__name__)


DEFAULT_CACHE_PATH = 'cache'

DEFAULT_REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:13.0) Gecko/20100101 Firefox/13.0.1',
}

last_url_request_datetime = None
DEFAULT_THROTTLE_DELTA = datetime.timedelta(seconds=30)


def wait_throttle(throttle_delta):
    if throttle_delta:
        global last_url_request_datetime
        while last_url_request_datetime and last_url_request_datetime > datetime.datetime.now() - throttle_delta:
            time.sleep(1)
        last_url_request_datetime = datetime.datetime.now()


def safe_filename(filename):
    filename = re.sub(r'[\\/]', r'.', filename)
    filename = re.sub(r' ', r'_', filename)
    return filename


def get_html_data(url, cached_filename=None, cache_path=DEFAULT_CACHE_PATH, headers=DEFAULT_REQUEST_HEADERS, throttle_delta=DEFAULT_THROTTLE_DELTA, download=True, **kwargs):
    log.debug("Request {0}".format(url))
    # If no specific cache filename - hash the url to generate an auto cache filename
    if not cached_filename:
        cached_filename = '{0}.html'.format(hashlib.sha1(url.encode('utf-8')).hexdigest())
    cached_filename = os.path.join(cache_path, safe_filename(cached_filename))
    if os.path.exists(cached_filename):
        log.debug('Cached %s' % cached_filename)
        html_data = open(cached_filename, 'rb').read()
    else:
        if not download:
            log.warn('Internet disbaled')
            return ''
        wait_throttle(throttle_delta)
        log.info('Read %s' % url)
        try:
            url_request = urllib.request.Request(url=url, headers=headers)
            url_request = urllib.request.urlopen(url_request)
            html_data = url_request.read()
            url_request.close()

            file = open(cached_filename, 'wb')
            file.write(html_data)
            file.close()
        except urllib.error.URLError:
            log.error(url)
            html_data = ''
    return html_data

try:
    from bs4 import BeautifulSoup
except ImportError:
    log.error('no bs4')
def get_html_soup(url, cached_filename, **kwargs):
    return BeautifulSoup(get_html_data(url, cached_filename, **kwargs))
    
