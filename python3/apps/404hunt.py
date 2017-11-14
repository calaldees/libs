import re
import requests
from bs4 import BeautifulSoup
from pprint import pprint
from collections import defaultdict
from unittest.mock import Mock

import logging
log = logging.getLogger(__name__)


def get_page_html(url):
    pass
    #response = 
    #raise PageError(url, )
    #return response.text


HOST = 'www.capitalfm.staging.int.thisisglobal.com'


def tidy_url(url):
    if not url:
        return
    re.sub(r'www\.capitalfm\.*?/', HOST, url)
    if url.startswith('/'):
        url = 'http://{}{}'.format(HOST, url)
    if HOST in url:
        return url


def crawl(source_host):
    to_crawl = set()
    crawled = set((None,))
    to_crawl.add(source_host)
    to_from = defaultdict(set)

    while to_crawl:
        if len(crawled) % 30 == 0:
            print('')
            print('Crawled: {} ToCrawl: {}'.format(len(crawled), len(to_crawl)))
        else:
            print('.', end="", flush=True)
        url = to_crawl.pop()
        try:
            response = requests.get(url, timeout=5)
        except requests.exceptions.TooManyRedirects:
            response = Mock()
            response.status_code = 666
        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
            response = Mock()
            response.status_code = 667
        crawled.add(url)
        if response.status_code < 200 or response.status_code >= 400:
            print('{}: {} -> {}'.format(response.status_code, to_from[url], url))
            continue
        soup = BeautifulSoup(response.text)

        page_links = {tidy_url(a.get('href')) for a in soup.findAll('a')}
        for url_to in page_links:
            to_from[url].add(url_to)
        to_crawl |= page_links - crawled

    pprint(crawled)


try:
    crawl('http://www.capitalfm.staging.int.thisisglobal.com/')
except:
    import sys, traceback, pdb
    type, value, tb = sys.exc_info()
    traceback.print_exc()
    pdb.post_mortem(tb)

