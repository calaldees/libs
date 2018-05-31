import random
from collections import namedtuple
from itertools import chain
from functools import partial, wraps
from unittest.mock import patch
import urllib.parse

from pyramid.httpexceptions import exception_response

import logging
log = logging.getLogger(__name__)


def patch_cache_bucket_decorator(acquire_cache_bucket_func=None):
    def f(_func):
        assert callable(acquire_cache_bucket_func)
        @wraps(_func)
        def wrapper(*args, **kwargs):
            request = args[0]
            with patch.object(request, 'cache_bucket', acquire_cache_bucket_func(request)):
                return _func(*args, **kwargs)
        return wrapper
    return f


def setup_pyramid_cache_manager(config):
    """
    Any view callable defined with the argument 'acquire_cache_manager_func'
    will automatically add a cache_manager to that request
    """

    #config.add_request_method(lambda request: null_cache_bucket, 'cache_bucket', property=True)

    def add_cache_bucket_to_request(view, info):
        acquire_cache_bucket_func = info.options.get('acquire_cache_bucket_func')
        def view_wrapper(context, request):
            if callable(acquire_cache_bucket_func):
                setattr(request, 'cache_bucket', acquire_cache_bucket_func(request))
            else:
                setattr(request, 'cache_bucket', null_cache_bucket)
            return view(context, request)
        return view_wrapper
    add_cache_bucket_to_request.options = ('acquire_cache_bucket_func', )
    config.add_view_deriver(add_cache_bucket_to_request, name='cache_bucket')

    def etag_handler(view, info):
        def view_wrapper(context, request):
            if (
                request.registry.settings.get('server.etag.enabled', False) and
                request.method == 'GET' and
                #hasattr(request, 'cache_bucket') and
                not isinstance(request.cache_bucket, NullCacheBucket) and
                not request.session.peek_flash()
            ):
                etag = urllib.parse.quote(request.cache_bucket.cache_key(request=request))
                if etag:
                    if etag in request.if_none_match:
                        log.debug(f'etag matched - aborting render - {etag}')
                        raise exception_response(304)
                    else:
                        log.debug(f'etag set - {etag}')
                        request.response.etag = (etag, False)  # The tuple and 'False' signifies a weak etag that can be gziped later
            return view(context, request)
        return view_wrapper
    config.add_view_deriver(etag_handler, name='etag', under='cache_bucket')


CacheFunctionWrapper = namedtuple('CacheFunctionWrapper', ('func', 'named_positional_args'))


class NullCacheBucket():
    def __init__(self, *args, **kwargs):
        pass

    def invalidate(self, **kwargs):
        pass

    def cache_key(self, **kwargs):
        return ''

    def get_or_create(self, bucket_name, data):
        return data
null_cache_bucket = NullCacheBucket()


class CacheBucket():

    @staticmethod
    def join_args_func(*args):
        return '-'.join(map(str, args))

    def __init__(self, bucket, version=None):
        self.version = int(version or random.randint(0, 2000000000))
        self.bucket = bucket
        self._func_store = {
            'invalidate_callbacks': [],
            'cache_key_generaters': []
        }
        self.register_cache_key_generator(self.join_args_func, ('bucket', 'version'))

    def _register_functionwrapper(self, _type, func, named_positional_args=()):
        self._func_store[_type].append(
            CacheFunctionWrapper(func, tuple(named_positional_args))
        )

    def _set_default_keys(self, kwargs):
        kwargs.setdefault('bucket', self.bucket)
        kwargs.setdefault('version', self.version)

    def _apply_funcs(self, _type, kwargs):
        self._set_default_keys(kwargs)
        required_arguments = set(chain.from_iterable(function_wrapper.named_positional_args for function_wrapper in self._func_store[_type]))
        assert kwargs.keys() >= required_arguments, f'CacheManager function executed with kwargs {kwargs.keys()} but required to pass {required_arguments}'
        return tuple(
            func(*(kwargs.get(attr) for attr in named_positional_args))
            for func, named_positional_args in self._func_store[_type]
        )

    def register_invalidate_callback(self, func, named_positional_args=()):
        self._register_functionwrapper('invalidate_callbacks', func, named_positional_args)

    def register_cache_key_generator(self, func, named_positional_args=()):
        self._register_functionwrapper('cache_key_generaters', func, named_positional_args)

    def invalidate(self, **kwargs):
        self._apply_funcs('invalidate_callbacks', kwargs)
        self.version += 1

    def cache_key(self, **kwargs):
        return self.join_args_func(*self._apply_funcs('cache_key_generaters', kwargs))


class CacheManager():

    def __init__(self, cache_store, default_cache_key_generators=(), default_invalidate_callbacks=()):
        #self.commit_func = commit_func
        self._cache_store = cache_store
        self._cache_buckets = {}
        self._default_cache_key_generators = list(default_cache_key_generators)
        self._default_invalidate_callbacks = list(default_invalidate_callbacks)

    def _create_bucket(self, bucket_name):
        cache_bucket = CacheBucket(bucket=bucket_name)

        # Default invalidators
        for invalidate_callback in self._default_invalidate_callbacks:
            cache_bucket.register_invalidate_callback(*invalidate_callback)
        cache_bucket.register_invalidate_callback(self._cache_store.delete, ('bucket', ))

        # Default cache_key_generators
        for cache_key_generator in self._default_cache_key_generators:
            cache_bucket.register_cache_key_generator(*cache_key_generator)

        cache_bucket.get_or_create = partial(self._cache_store.get_or_create, bucket_name)
        return cache_bucket

    def get(self, bucket_name):
        if bucket_name not in self._cache_buckets:
            self._cache_buckets[bucket_name] = self._create_bucket(bucket_name)
        return self._cache_buckets[bucket_name]
