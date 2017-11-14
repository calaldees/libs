#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

import re
import copy
from functools import lru_cache

import pyramid.request
import pyramid.response
import pyramid.events
import pyramid.decorator

import logging
log = logging.getLogger(__name__)

from ..misc import json_object_handler

#-------------------------------------------------------------------------------
# Constants
#-------------------------------------------------------------------------------

#FORMAT_REQUEST_ACCEPT = {
#    'text/html': 'html',
#    'text/csv': 'csv',
#    'text/plain': 'csv',
#    'text/javascript': 'json',
#    'application/json': 'json',
#    'text/xml': 'xml',
#    'application/xml': 'xml',
#    'application/atom+xml': 'rss',
#    'application/xml+rss': 'rss',
#    'application/pdf': 'pdf',
#}

#-------------------------------------------------------------------------------
# Class's
#-------------------------------------------------------------------------------

class FormatError(Exception):
    pass


#-------------------------------------------------------------------------------
# Action Returns
#-------------------------------------------------------------------------------

def action_ok(message='', data={}, code=200, status='ok', **kwargs):
    assert isinstance(message, str)
    assert isinstance(data, dict)
    assert isinstance(code, int)
    d = {
        'status': status,
        'messages': [],
        'data': data,
        'code': code,
    }
    d.update(kwargs)
    if message:
        d['messages'].append(message)
    return d


class action_error(Exception):
    def __init__(self, message='', data={}, code=500, status='error', **kwargs):
        super().__init__(self, message)
        self.d = action_ok(message=message, data=data, code=code, status=status, **kwargs)
    def __str__( self ):
        return str(self.d)


#-------------------------------------------------------------------------------
# Register Format Mechanics
#-------------------------------------------------------------------------------

class FormatRendererManager():

    def __init__(self):
        self._renderers = {}
        self._content_type_to_format = {}
        self._format_to_content_type = {}

    @property
    def registered_formats(self):
        return self._renderers.keys()

    @pyramid.decorator.reify
    def registered_formats_regex(self):
        return re.compile(r'\.(?P<format>{})$'.format('|'.join(self.registered_formats)), flags=re.IGNORECASE)

    def register_format_decorator(self, format_name, content_type=None):
        assert isinstance(format_name, str)
        assert format_name not in self._renderers
        if content_type:
            assert isinstance(content_type, str)
            assert content_type not in self._content_type_to_format
            self._content_type_to_format[content_type] = format_name
            self._format_to_content_type[format_name] = content_type
        def wrapper(format_func):
            assert callable(format_func)
            self._renderers[format_name] = format_func
        return wrapper

    def render(self, request, data):
        format_name = data['format']
        response = self._renderers[format_name](request, data)
        # Override context type
        if hasattr(response, 'content_type') and self._format_to_content_type.get(format_name):
            response.content_type = self._format_to_content_type[format_name]
        return response

format_manager = FormatRendererManager()


def before_traversal_extract_format_from_path_info_to_get_param(event):
    """
    We could have a path_info of '/track/t3.json'
    We don't want '.json' contaminating the traversal algorithm
    Use a regex to extract the format from the path_info to a GET param
    """
    path_format_match = format_manager.registered_formats_regex.search(event.request.path_info)
    if path_format_match:
        event.request.GET.update(path_format_match.groupdict())
        event.request.path_info = format_manager.registered_formats_regex.sub('', event.request.path_info)


def requested_response_format(request):
    formats = set(filter(None, (
        request.params.get('format'),  # From GET/POST params (augmented by BeforeTraversal)
        request.matchdict.get('format') if request.matchdict else None,  # matched route 'format' key
    ))) or set(filter(None, (
        format_manager._content_type_to_format.get(  # content_type from 'Accept' header
            request.accept.best_match(format_manager._content_type_to_format.keys())
        ),
    ))) or {
        request.registry.settings.get('api.format.default', 'html'),
    }
    if len(formats) >= 2:
        raise Exception(f'Multiple formats requested {formats}')
    return formats.pop()


def setup_pyramid_autoformater(config):
    config.add_subscriber(before_traversal_extract_format_from_path_info_to_get_param, pyramid.events.BeforeTraversal)
    config.add_request_method(requested_response_format, 'requested_response_format', property=True)

    #config.add_response_adapter(autoformat_response_adaptor, dict)
    #def autoformat_format_selector_response_callback(request, response):
    #    if isinstance(response, dict):
    #        response['format'] = request.requested_response_format
    #def add_response_callbacks_to_newrequest(event):
    #    event.request.add_response_callback(autoformat_format_selector_response_callback)
    #config.add_subscriber(add_response_callbacks_to_newrequest, pyramid.events.NewRequest)

    def autoformat_view(view, info):
        if info.options.get('autoformat', True):
            def view_wrapper(context, request):
                try:
                    response = view(context, request)  # Execute View
                except action_error as ae:
                    response = ae.d
                if isinstance(response, dict) and response.keys() >= {'code', 'messages', 'data', 'status'}:
                    if hasattr(request, 'session_identity'):
                        # TODO: I wanted the session_identity to be decoupled from autoformater
                        response['identity'] = request.session_identity
                    if getattr(request, 'context', None) and hasattr(request.context, 'name'):
                        response['context'] = request.context.name
                    response['format'] = request.requested_response_format
                    return format_manager.render(request, response)
                return response
            return view_wrapper
        return view
    autoformat_view.options = ('autoformat', )
    config.add_view_deriver(autoformat_view, over='mapped_view', under='rendered_view')


def autoformat_response_adaptor(data):
    pass


#-------------------------------------------------------------------------------
# Decorator
#-------------------------------------------------------------------------------

#@decorator
def auto_format_output(target, *args, **kwargs):
    """
    A decorator to decarate a Pyramid view

    The view could return a plain python dict

    it will try to:
     - extract a sutable format string from the URL e.g html,json,xml,pdf,rss,etc
     - apply a format function to the plain python dict return
    """
    # Extract request object from args
    request = request_from_args(args)
    request.matchdict = request.matchdict if request.matchdict else {}
    if 'internal_request' in request.matchdict:  # Abort if internal call
        return target(*args, **kwargs)

    # Pre Processing -----------------------------------------------------------

    # Find format string 'format' based on input params, to then find a render func 'formatter'  - add potential formats in order of precidence
    # TODO: THis is RUBBISH!! .. if we dont return the format that is expected ... exception!!
    formats = []
    # add kwarg 'format'
    try: formats.append(kwargs['format'])
    except: pass
    # From GET/POST params
    try: formats.append(request.params['format'])
    except: pass
    # matched route 'format' key
    try: formats.append(request.matchdict['format'])
    except: pass
    # add 'format' from URL path
    try: formats.append(format_regex_path.match(request.path).group('format'))
    except: pass
    # add 'format' from URL query string
    try: formats.append(format_regex_qs.match(request.path_qs).group('format'))
    except: pass
    # add 'format' from request content type
    # Possible bug: This could lead to caching inconsitencys as etags and other caching must key the 'request-accept' before this is enabled
    #try   : formats.append(format_request_accept[request.accept.header_value.split(',')[0]])
    #except: pass
    # add default format
    formats.append()
    formats = [format for format in formats if format]  # remove any blank entries in formats list

    request.matchdict['format'] = formats[0]  # A way for all methods wraped by this decorator to determin what format they are targeted for

    # Execute View ------------------------------------------------------------------
    try:
        result = target(*args, **kwargs)
    except action_error as ae:
        result = ae.d
        #log.warn("Auto format exception needs to be handled")

    # Post Processing ----------------------------------------------------------

    # the result may have an overriding format that should always take precident
    try: formats.insert(0,result['format'])
    except: pass

    # Attempt auto_format if result is a plain python dict and auto_format func exisits
    if isinstance(result, dict):
        # Add pending flash messages to result dict
        result['messages'] = result.get('messages',[])
        if request.session.peek_flash():
            result['messages'] += request.session.pop_flash()

        for formatter in filter(lambda i: i, [_auto_formaters.get(format) for format in formats]):
            try:
                # Format result dict using format func
                response = formatter(request, result)
                break
            except FormatError:
                log.warn('format refused')
                # TODO - useful error message .. what was the exceptions message
            except Exception:
                log.warn('format rendering erorrs', exc_info=True)
        else:
            # TODO: This is rubish .. the original exception is obscured and needs to be surfaced
            raise Exception('no format was able to render')

        # Set http response code
        if isinstance(response, pyramid.response.Response) and result.get('code'):
            response.status_int = result.get('code')

        request.response = response
        result = response

    return result


#-------------------------------------------------------------------------------
# Renderer Template
#-------------------------------------------------------------------------------
from pyramid.renderers import render_to_response
import os.path

def render_template(request, data, template_language='mako'):
    assert data.keys() >= {'format', 'context'}
    return render_to_response(
        os.path.join(data['format'], '{}.{}'.format(data['context'], template_language)),
        data,
        request=request,
        #response=request.response,
    )

#-------------------------------------------------------------------------------
# Formatters
#-------------------------------------------------------------------------------

@format_manager.register_format_decorator('python')
def format_python(request, data):
     return data


import json
@format_manager.register_format_decorator('json', content_type='application/json')
def format_json(request, data):
    return pyramid.response.Response(
        body=json.dumps(data, default=json_object_handler),
        charset='utf-8'
    )


from ..xml import dictToXMLString
@format_manager.register_format_decorator('xml', content_type='text/xml')
def format_xml(request, data):
    return pyramid.response.Response(
        body='<?xml version="1.0" encoding="UTF-8"?>'.encode('utf-8') + dictToXMLString(data),
        charset='utf-8',
    )

# # RSS -------------------------------
# def format_rss(request, result):
#     response = render_template(request, result, 'rss')
#     request.response.content_type = "application/rss+xml; charset=utf-8"
#     return response
# register_formater('rss', format_rss)

# # GRAPH ------------------------------
# def format_graph(request, result):
#     request.response = render_template(request, result, 'graph')
#     return request.response
# register_formater('graph', format_graph)

# # HTML ------------------------------
@format_manager.register_format_decorator('html', content_type='text/html')
def format_html(request, data):
     return render_template(request, data)
# register_formater('html', format_html)
# def format_html_template(request, result):
#     """
#     Return html content with no head/body tags
#     Base templates must support result['format'] for this to function
#     """
#     result['format'] = 'html_template'
#     return format_html(request, result)
# register_formater('html_template', format_html_template)


# # Redirect---------------------------
# from pyramid.httpexceptions import HTTPFound
# def format_redirect(request, result):
#     """
#     A special case for compatable browsers making REST calls
#     """
#     if request.response.headers.get('Set-Cookie'):
#         raise FormatError('format_redirect cannot function when cookies are being set')
#     for message in result['messages']:
#         request.session.flash(message)
#     del result['code']
#     return HTTPFound(location=request.referer)
# register_formater('redirect', format_redirect)

