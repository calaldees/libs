import datetime
import statistics
from typing import NamedTuple
from collections.abc import MutableSequence
from urllib.request import urlopen, Request
import urllib.error
from http.client import HTTPResponse
from functools import reduce
from time import sleep
import logging

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


class RequestStats(NamedTuple):
    time_start: datetime.datetime
    time_end: datetime.datetime
    code: int

    @property
    def duration(self) -> datetime.timedelta:
        return self.time_end - self.time_start

    @property
    def isError(self) -> bool:
        return self.code >= 400 and self.code < 600


class RequestsStats(NamedTuple):
    requests: MutableSequence[RequestStats] = []

    def __str__(self):
        return f'{self.duration_average=} {self.count_error=} {self.count=}'

    @property
    def count(self) -> int:
        return len(self.requests)

    @property
    def duration_average(self) -> float:
        return statistics.mean(r.duration.microseconds for r in self.requests)

    @property
    def count_error(self) -> int:
        def _reducer(acc, i):
            acc += 1 if i.isError else 0
            return acc
        return reduce(_reducer, self.requests, 0)



def monitor(request: Request, rate: datetime.timedelta=datetime.timedelta(seconds=5)) -> RequestsStats:
    time_start = datetime.datetime.now()
    stats = RequestsStats()
    running = True
    while running:
        try:
            code = 0
            request_time_start = datetime.datetime.now()
            try:
                with urlopen(request, timeout=rate.total_seconds()) as response:
                    #response.read()
                    code = response.code
            except urllib.error.HTTPError as ex:
                code = ex.status
            except urllib.error.URLError as ex:
                code = 500
            request_time_end = datetime.datetime.now()
            request_stats = RequestStats(request_time_start, request_time_end, code)
            stats.requests.append(request_stats)
            log.info(request_stats)

            _sleep = (datetime.datetime.now() - time_start).total_seconds() % rate.total_seconds()
            log.info(f'{_sleep=}')
            sleep(_sleep)
        except KeyboardInterrupt:
            running = False
    return stats


if __name__ == '__main__':
    gql = 'query {audiences {id name}}'
    request = Request('https://athena.diginf.musicradio.com/graphql', method='POST', data='{"query": "__GQL__"}'.replace('__GQL__', gql).encode('utf8'))
    stats = monitor(request)
    print(stats)
