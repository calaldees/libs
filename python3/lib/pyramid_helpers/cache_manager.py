import random
from collections import namedtuple
from itertools import chain
from functools import partial


def setup_pyramid_cache_manager(config):
    """
    Any view callable defined with the argument 'acquire_cache_manager_func'
    will automatically add a cache_manager to that request
    """

    def add_cache_manager_to_request(view, info):
        acquire_cache_manager_func = info.options.get('acquire_cache_manager_func')
        if not callable(acquire_cache_manager_func):
            return view
        def view_wrapper(context, request):
            setattr(request, 'cache_manager', acquire_cache_manager_func(request))
            return view(context, request)
        return view_wrapper
    add_cache_manager_to_request.options = ('acquire_cache_manager_func', )
    config.add_view_deriver(add_cache_manager_to_request)

    def etag_handler(view, info):
        def view_warpper(context, request):

        return view
    config.add_view_deriver(etag_handler)


def etag(request, cache_key=_generate_cache_key_default):
    if request.registry.settings.get('server.etag.enabled'):
        try:
            etag = cache_key(request)
        except TypeError:  # If we cant run it, then it's probably they key
            etag = cache_key
        except LookupError:
            log.debug('etag generation aborted, unique response detected')
            etag = None
        except Exception:
            log.debug('etag generation aborted, unable to generate etag')
            etag = None
        if etag:
            etag += request.registry.settings.get('server.etag.cache_buster','')
            if etag in request.if_none_match:
                log.debug('etag matched - aborting render - %s' % etag)
                raise exception_response(304)
            else:
                log.debug('etag set - %s' % etag)
                request.response.etag = (etag, False)  # The tuple and 'False' signifys a weak etag that can be gziped later



CacheFunctionWrapper = namedtuple('CacheFunctionWrapper', ('func', 'named_positional_args'))


class CacheBucket():

    @staticmethod
    def join_args_func(*args):
        return '-'.join(map(str(args)))

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
            self.CacheFunctionWrapper(func, tuple(named_positional_args))
        )

    def _set_default_keys(self, kwargs):
        kwargs.setdefault('bucket', self.bucket)
        kwargs.setdefault('version', self.version)

    def _apply_funcs(self, _type, kwargs):
        self._set_default_keys(kwargs)
        required_arguments = set(chain.from_iterable(function_wrapper.named_positional_args for function_wrapper in self._func_store[_type]))
        assert required_arguments >= kwargs.keys(), f'CacheManager function executed with kwargs {kwargs.keys()} but required to pass {required_arguments}'
        return (
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

    def __init__(self, cache_store, default_cache_key_generators=()):  #commit_func,
        #self.commit_func = commit_func
        self._cache_store = cache_store
        self._cache_buckets = {}
        self._default_cache_key_generators = list(default_cache_key_generators)

    def _create_item(self, bucket):
        cache_bucket = CacheBucket(bucket=bucket)
        #cm.register_invalidate_callback(self.commit_func)
        cache_bucket.register_invalidate_callback(self.cache_store.delete, ('bucket', ))
        for cache_key_generator in self._default_cache_key_generators:
            cache_bucket.register_cache_key_generator(*cache_key_generator)
        cache_bucket.get_or_create = partial(self.cache.get_or_create, bucket)
        return cache_bucket

    def get(self, bucket):
        if bucket not in self._cache_buckets:
            self._cache_buckets[bucket] = self._create_buckets(bucket)
        return self._cache_buckets[bucket]
