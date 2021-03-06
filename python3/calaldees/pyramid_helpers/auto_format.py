# DEPRECATED - Use auto_format2


#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

from decorator import decorator
import re
import copy

import pyramid.request
import pyramid.response

import logging
log = logging.getLogger(__name__)

from . import request_from_args

#-------------------------------------------------------------------------------
# Constants
#-------------------------------------------------------------------------------

# Regex to extract 'format' from request URL
format_regex_path = re.compile(r'.*\.(?P<format>.*?)($|\?|#)', flags=re.IGNORECASE)
format_regex_qs = re.compile(r'.*(^|,)format=(?P<format>.*?)($|,)', flags=re.IGNORECASE)  # AllanC - this could be replaced at a later date when web_params_to_kwargs is implemented , used to use r'.*\?.*format=(.*?)($|,)' for whole url
format_request_accept = {
    'text/html'           : 'html',
    'text/csv'            : 'csv' ,
    'text/plain'          : 'csv' ,
    'text/javascript'     : 'json',
    'application/json'    : 'json',
    #'text/xml'            : 'xml' ,
    #'application/xml'     : 'xml' ,
    'application/atom+xml': 'rss' ,
    'application/xml+rss' : 'rss' ,
    'application/pdf'     : 'pdf' ,
}


#-------------------------------------------------------------------------------
# Class's
#-------------------------------------------------------------------------------

class FormatError(Exception):
    pass


#-------------------------------------------------------------------------------
# Setup
#-------------------------------------------------------------------------------

_auto_formaters = {}


def register_formater(format_name, format_func):
    """
    Register a format processor with a key
    e.g
    register_formater('json', dict_to_json_response_func)

    the format func could look up templates or call other libs to process the return

    format_funcs should return a Pyramid Response object
    """
    assert isinstance(format_name, str )
    assert callable(format_func)
    _auto_formaters[format_name] = format_func


def registered_formats():
    return _auto_formaters.keys()


#-------------------------------------------------------------------------------
# Route Creator helper
#-------------------------------------------------------------------------------

def append_format_pattern(route):
    """
    to be used like:
        config.add_route('home'          , append_format_pattern('/')              )
        config.add_route('track'         , append_format_pattern('/track/{id}')    )
    """
    return re.sub(r'{(.*)}', r'{\1:[^/\.]+}', route) + r'{spacer:[.]?}{format:(%s)?}' % '|'.join(registered_formats())


#-------------------------------------------------------------------------------
# Decorator
#-------------------------------------------------------------------------------

@decorator
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
    formats.append(request.registry.settings.get('api.format.default', 'html'))
    formats = [format for format in formats if format]  # remove any blank entries in formats list

    request.matchdict['format'] = formats[0]  # A way for all methods wraped by this decorator to determin what format they are targeted for

    # Execute ------------------------------------------------------------------
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
        self.d = action_ok(message=message, data=data, code=code, status=status, **kwargs)
    def __str__( self ):
        return str(self.d)


#-------------------------------------------------------------------------------
# Renderer Template
#-------------------------------------------------------------------------------
from pyramid.renderers import render_to_response
import os.path

def render_template(request, result, format, template_data_param='d'):
    #template_params = {template_data_param:result}
    #template_params.update(request.matchdict)
    template_filename = ''
    try:
        template_filename = request.matched_route.name
    except AttributeError:
        pass
    try:
        template_filename = request.context.template
    except AttributeError:
        pass
    response = render_to_response(
        '%s.mako' % (os.path.join(format, template_filename)),
        result,
        request=request,
        response=request.response,
    )
    return response

#-------------------------------------------------------------------------------
# Formatters
#-------------------------------------------------------------------------------

# Python dict formater -------------
register_formater('python', lambda result:result)

# JSON -----------------------------
from ..json import json_string
def format_json(request, result):
    request.response.text = json_string(result)
    request.response.content_type = "application/json; charset=utf-8"
    return request.response
register_formater('json', format_json)

# XML -------------------------------
from ..xml import dictToXMLString
def format_xml(request, result):
    xml_head = '<?xml version="1.0" encoding="UTF-8"?>'.encode('utf-8')
    request.response.body = xml_head + dictToXMLString(result)
    request.response.content_type = "text/xml; charset=utf-8"
    return request.response
register_formater('xml', format_xml)

# RSS -------------------------------
def format_rss(request, result):
    response = render_template(request, result, 'rss')
    request.response.content_type = "application/rss+xml; charset=utf-8"
    return response
register_formater('rss', format_rss)

# GRAPH ------------------------------
def format_graph(request, result):
    request.response = render_template(request, result, 'graph')
    return request.response
register_formater('graph', format_graph)

# HTML ------------------------------
def format_html(request, result):
    request.response = render_template(request, result, 'html')
    return request.response
register_formater('html', format_html)
def format_html_template(request, result):
    """
    Return html content with no head/body tags
    Base templates must support result['format'] for this to function
    """
    result['format'] = 'html_template'
    return format_html(request, result)
register_formater('html_template', format_html_template)


# Redirect---------------------------
from pyramid.httpexceptions import HTTPFound
def format_redirect(request, result):
    """
    A special case for compatable browsers making REST calls
    """
    if request.response.headers.get('Set-Cookie'):
        raise FormatError('format_redirect cannot function when cookies are being set')
    for message in result['messages']:
        request.session.flash(message)
    del result['code']
    return HTTPFound(location=request.referer)
register_formater('redirect', format_redirect)

