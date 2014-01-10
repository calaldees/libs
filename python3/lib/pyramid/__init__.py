from decorator import decorator
import pyramid.request
import pyramid.registry

import logging
log = logging.getLogger(__name__)



def request_from_args(args):
    # Extract request object from args
    for arg in args:
        if isinstance(arg, pyramid.request.Request):
            return arg
    raise Exception('no pyramid.request.Request in args')


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
    """
    request_from_args(args).matchdict['internal_request'] = True
    return target(*args, **kwargs)

@decorator
def gzip(target, *args, **kwargs):
    """
    The base instructions to be executed for most calls
    """
    request = request_from_args(args)
    
    # Abort if internal call
    if 'internal_request' in request.matchdict:
        return target(*args, **kwargs)

    # Enable Pyramid GZip on all responses - NOTE! In a production this should be handled by nginx for performance!
    if request.registry.settings.get('server.gzip'):
        request.response.encode_content(encoding='gzip', lazy=False)
    
    result = target(*args, **kwargs)
    
    return result

#-------------------------------------------------------------------------------
# Predicates
#-------------------------------------------------------------------------------

def method_delete_router(info, request):
    if request.method == 'DELETE' or request.params.get('method','GET').upper() == 'DELETE':
        return True

def method_put_router(info, request):
    if request.method == 'PUT' or request.params.get('method','GET').upper() == 'PUT':
        return True

