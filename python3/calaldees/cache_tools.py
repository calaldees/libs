import datetime
from pathlib import Path
import pickle
import hashlib


class CacheProxy():
    def __init__(self, acquire_data_function, path=Path('_cache'), cache_only=False, ttl=datetime.timedelta(days=1)):
        assert callable(acquire_data_function)
        self.acquire_data_function = acquire_data_function
        self.path = path
        self.path.mkdir(exist_ok=True)
        self.cache_only = cache_only
        assert ttl.seconds
        self.ttl = ttl
    def acquire(self, *args, **kwargs):
        cache = self.path.joinpath(hashlib.sha1(pickle.dumps((args, kwargs))).hexdigest())
        if cache.is_file() and (datetime.datetime.fromtimestamp(cache.stat().st_mtime) > datetime.datetime.now() - self.ttl):
            with cache.open(mode='rb') as f:
                return f.read()
        if self.cache_only:
            return
        data = self.acquire_data_function(*args, **kwargs)
        with cache.open(mode='wb') as f:
            f.write(data)
        return data
