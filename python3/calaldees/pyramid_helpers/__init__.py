import logging
log = logging.getLogger(__name__)


try:
    from decorator import decorator
except ImportError:
    log.error('Library not present')
    def decorator(*args, **kwargs):
        return args[0]

import pyramid.request
import pyramid.threadlocal

from ..json import json_string


def request_from_args(args):
    # Extract request object from args
    for arg in args:
        if isinstance(arg, pyramid.request.Request):
            return arg
    raise Exception('no pyramid.request.Request in args')


def get_setting(key):
    """
    convenience global settings
    """
    return pyramid.threadlocal.get_current_registry().settings.get(key)


#-------------------------------------------------------------------------------
# Web view decorators
#-------------------------------------------------------------------------------

@decorator
def mark_external_request(target, *args, **kwargs):
    """
    All the decorators fire on almost every call.
    If we have 'internal_request' in our request, then most of the decorators should short circit and abort.
    this enables us to use internal API calls.
    decorators that may still fire for internal calls are things like cache lookup
    This should be the absolute closest decorator to the actual method call as possible

    TODO: This is horrible ... can we do this in a better way?
    """
    try:
        request_from_args(args).matchdict['internal_request'] = True
    except Exception:
        pass
    return target(*args, **kwargs)


@decorator
def gzip(target, *args, **kwargs):
    """
    The base instructions to be executed for most calls
    """
    request = request_from_args(args)

    # Abort if internal call
    if 'internal_request' in (request.matchdict or {}):
        return target(*args, **kwargs)

    result = target(*args, **kwargs)

    # Enable Pyramid GZip on all responses - NOTE! In a production this should be handled by nginx for performance!
    if request.registry.settings.get('server.gzip') and 'gzip' in request.headers.get('Accept-Encoding',''):
        request.response.encode_content(encoding='gzip', lazy=False)

    return result


# TODO: Depricated
def _generate_max_age_seconds_default(request):
    return request.registry.settings.get('server.max_age.default')
def max_age(gen_max_age_seconds=_generate_max_age_seconds_default, **options):
    """
    Decorator to set cache_expires
    """
    def _max_age(target, *args, **kwargs):
        request = request_from_args(args)
        if 'internal_request' in request.matchdict:  # Abort if internal call
            return target(*args, **kwargs)

        _return = target(*args, **kwargs)  # Execute the wrapped function

        if hasattr(gen_max_age_seconds, '__call__'):
            max_age_seconds = gen_max_age_seconds(request)
        else:
            max_age_seconds = gen_max_age_seconds
        if max_age_seconds:
            _return.cache_expires(max_age_seconds, **options)

        return _return
    return decorator(_max_age)


#-------------------------------------------------------------------------------
# Predicates
#-------------------------------------------------------------------------------

class MethodRouterPredicate(object):
    def __init__(self, request_method, config):
        """
        Allow a query_string `method=DELETE` to allow a delete request to be faked with a GET
        """
        self.request_method = request_method.upper()
        assert self.request_method in {'DELETE', 'PUT'}

    def text(self):
        return f'upgrade_get_with_param_to = {self.request_method}'

    phash = text

    def __call__(self, context_or_info, request):
        return self.request_method in (
            request.method.upper(),
            request.params.get('method', 'GET').upper()
        )


class RequiresParamPredicate(object):
    def __init__(self, val, config):
        self.param_name = val

    def text(self):
        return f'requires_param = {self.param_name}'

    phash = text

    def __call__(self, context_or_info, request):
        return request.params.get(self.param_name)


#-------------------------------------------------------------------------------
# Headers
#-------------------------------------------------------------------------------

def set_cookie(request, name, data, path='/'):
    """
    (Hand rolled json cookie setter because webob had crazy encode issues)
    """
    request.response.headerlist.append((
        'Set-Cookie', '{name}={json_string}; Path={path}'.format(
            name=name,
            path=path,
            json_string=json_string(data),
        )
    ))
