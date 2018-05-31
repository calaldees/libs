import sys
import re
import requests
import datetime
from collections import namedtuple
from bs4 import BeautifulSoup
import traceback
import pdb
import urllib.parse


import logging
log = logging.getLogger(__name__)


VERSION = '0.0'

DEFAULT_EXCLUDE_REGEX = [
    r'^http:',
    r'.*\.(mp4|srt|ssa|mp3|avi|mkv)$'
]

Redirect = namedtuple('Redirect', ['redirect_url'])
CrawlStatus = namedtuple('CrawlStatus', ['crawled', 'to_crawl', 'failed', 'ignored'])


def requests_get(url):
    response = requests.get(url)
    return response.text


class CrawlStats(object):
    def __init__(self):
        self.time_start = datetime.datetime.now()
        self.time_end = datetime.datetime.now()
        self.crawled = set()

    @property
    def num_pages(self):
        return len(self.crawled)

    @property
    def time_taken(self):
        return self.time_end - self.time_start


def crawl(root_url, func_get_html, exclude_regex=[]):
    """
    """

    def ignore_url(url):
        for regex in exclude_regex:
            if re.match(regex, url):
                return True
        return False

    to_crawl = set()
    crawled = {'', None}
    failed = set()
    ignored = set()

    to_crawl.add(root_url)

    while to_crawl:
        url = to_crawl.pop()

        if url != root_url:
            # Abort on exclude match
            if ignore_url(url):
                ignored.add(url)
                continue
            if url.startswith('/'):
                #url = '{0}{1}'.format(root_url, url)
                url = urllib.parse.urljoin(root_url, url)

        try:
            page_html = func_get_html(url)
        except Exception as e:
            page_html = ''
            log.warn(e)
            failed.add(url)
        #if hasattr(page_html, 'redirect_url'):
        #    to_crawl.add(page_html.redirect_url)
        #    continue
        crawled.add(url)
        if not page_html:
            continue
        soup = BeautifulSoup(page_html)
        to_crawl |= {a.get('href') for a in soup.findAll('a')} - crawled
        yield CrawlStatus(crawled, to_crawl, failed, ignored)


def crawl_manager(url, func_get_html, exclude_regex=[]):
    crawl_return = CrawlStats()
    last_crawl_count = 0
    for crawl_status in crawl(url, func_get_html, exclude_regex):
        crawl_count = len(crawl_status.crawled)
        if crawl_count > last_crawl_count:
            sys.stdout.write('.')
            sys.stdout.flush()
            last_crawl_count = crawl_count
            crawl_return.crawled = crawl_status.crawled
    crawl_return.time_end = datetime.datetime.now()
    return crawl_return


def get_args():
    import argparse
    parser = argparse.ArgumentParser(
        description="""
        """,
        epilog=""" """
    )

    parser.add_argument('url', action='store', help='Target url to crawl')

    parser.add_argument('-v', '--verbose', action='store_true', help='', default=False)
    parser.add_argument('--version', action='version', version=VERSION)

    args = vars(parser.parse_args())

    return args


def main():
    args = get_args()
    logging.basicConfig(level=logging.DEBUG if args['verbose'] else logging.WARN)

    try:
        crawl_manager(args['url'], requests_get, DEFAULT_EXCLUDE_REGEX)
    except:
        type, value, tb = sys.exc_info()
        traceback.print_exc()
        pdb.post_mortem(tb)


if __name__ == "__main__":
    main()
