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


# -----------------------------------

class PostViewDictAugmentation():
    def __init__(self):
        self._pre_render_funcs = []
        self._post_render_funcs = []

    def register_pre_render_decorator(self):
        def wrapper(augmenter_func):
            assert callable(augmenter_func)
            self._pre_render_funcs.append(augmenter_func)
        return wrapper

    def register_post_render_decorator(self):
        def wrapper(augmenter_func):
            assert callable(augmenter_func)
            self._post_render_funcs.append(augmenter_func)
        return wrapper

    def pre_render_augmentation(self, request, response):
        for _func in self._pre_render_funcs:
            _func(request, response)

    def post_render_augmentation(self, request, response, response_object):
        for _func in self._post_render_funcs:
            _func(request, response, response_object)


post_view_dict_augmentation = PostViewDictAugmentation()


@post_view_dict_augmentation.register_post_render_decorator()
def overlay_return_code_on_response_object(request, response, response_object):
    if isinstance(response_object, pyramid.response.Response):
        response_object.status_int = response.get('code')


@post_view_dict_augmentation.register_pre_render_decorator()
def add_template_to_response(request, response):
    try:
        response.setdefault('template', request.context.__template__)
    except AttributeError:
        pass

@post_view_dict_augmentation.register_pre_render_decorator()
def add_format_to_response(request, response):
    try:
        response.setdefault('format', request.requested_response_format)
    except AttributeError:
        pass

# TODO: move this to the session to reduce coupling
@post_view_dict_augmentation.register_pre_render_decorator()
def add_identity_to_response(request, response):
    if hasattr(request, 'session_identity'):
        response['identity'] = request.session_identity

# TODO: Move this to reduce coupling
@post_view_dict_augmentation.register_pre_render_decorator()
def add_messages_in_session_to_response(request, response):
    if request.session.peek_flash():
        # TODO: This needs to be modularised
        response.setdefault('messages', []).append(request.session.pop_flash())


# -----------------------


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
        # TODO: BUG: I don't think this html fallback works - a None content_type in `best_match` above defualts to the order they are registed in the `format_manager`
        request.registry.settings.get('api.format.default', 'html'),
    }
    if len(formats) >= 2:
        raise Exception(f'Multiple formats requested {formats}')
    return formats.pop()


def setup_pyramid_autoformater(config):
    config.add_subscriber(before_traversal_extract_format_from_path_info_to_get_param, pyramid.events.BeforeTraversal)
    config.add_request_method(requested_response_format, 'requested_response_format', property=True)  # TODO: could we use reify here? Do views modify this anywhere?

    #config.add_response_adapter(autoformat_response_adaptor, dict)
    #def autoformat_format_selector_response_callback(request, response):
    #    if isinstance(response, dict):
    #        response['format'] = request.requested_response_format
    #def add_response_callbacks_to_newrequest(event):
    #    event.request.add_response_callback(autoformat_format_selector_response_callback)
    #config.add_subscriber(add_response_callbacks_to_newrequest, pyramid.events.NewRequest)

    def autoformat_view(view, info):
        if not info.options.get('autoformat', True):
            return view
        def view_wrapper(context, request):
            #if 'internal_request' in request.matchdict:  # Abort if internal call
            #    return view(context, request)
            try:
                response = view(context, request)  # Execute View
            except action_error as ae:
                response = ae.d
            if isinstance(response, dict) and response.keys() >= {'code', 'messages', 'data', 'status'}:
                response = copy.copy(response)  # HACK: BUGFIX: dogpile in_python cache dicts were being modified on return
                post_view_dict_augmentation.pre_render_augmentation(request, response)
                response_object = format_manager.render(request, response)
                post_view_dict_augmentation.post_render_augmentation(request, response, response_object)
                return response_object
            return response
        return view_wrapper
    autoformat_view.options = ('autoformat', )
    config.add_view_deriver(autoformat_view, name='autoformat', over='mapped_view', under='rendered_view')


#-------------------------------------------------------------------------------
# Renderer Template
#-------------------------------------------------------------------------------
from pyramid.renderers import render_to_response
import os.path

def render_template(request, data, template_language='mako'):
    assert data.keys() >= {'format', 'template'}
    return render_to_response(
        os.path.join(data['format'], '{}.{}'.format(data['template'], template_language)),
        data,
        request=request,
        response=request.response,
    )

#-------------------------------------------------------------------------------
# Formatters
#-------------------------------------------------------------------------------

@format_manager.register_format_decorator('python')
def format_python(request, data):
     return data


@format_manager.register_format_decorator('html', content_type='text/html')
def format_html(request, data):
     return render_template(request, data)


import json
@format_manager.register_format_decorator('json', content_type='application/json')
def format_json(request, data):
    request.response.text = json.dumps(data, default=json_object_handler)
    return request.response
    #charset='utf-8',


from ..xml import dictToXMLString
@format_manager.register_format_decorator('xml', content_type='text/xml')
def format_xml(request, data):
    request.response.text = '<?xml version="1.0" encoding="UTF-8"?>'.encode('utf-8') + dictToXMLString(data)
    return request.response
    #charset='utf-8',


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
