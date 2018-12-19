from os import environ
import re
from functools import partial


def _render_env(value, _get_env, **kwargs):
    """
    >>> _render_env(
    ...     '''My value is {value} and it is {overlay}''',
    ...     partial(get_env, _environ={
    ...         'value': 'bob',
    ...     }),
    ...     overlay='cool',
    ... )
    'My value is bob and it is cool'
    """
    value_sub_keys = tuple(match.group(1) for match in re.finditer(r'{(.*?)}', value))
    return value.format(**{
        value_sub_key: _get_env(value_sub_key, **kwargs)
        for value_sub_key in value_sub_keys
    })


def get_env(key, _environ=environ, _environ_templates={}, _post_render_funcs={}, _fallback_separator=None, **kwargs):
    """
    >>> get_env(
    ...     'IMAGE_API', 
    ...     _environ={},
    ...     _environ_templates={},
    ... )
    Traceback (most recent call last):
        ...
    AssertionError: unknown environ key: IMAGE_API
    assert 'IMAGE_API' in {}

    >>> get_env(
    ...     'IMAGE_API', 
    ...     _environ={
    ...         'IMAGE_PREFIX': 'gitlab.company.co.uk:1234/ci-testing',
    ...     }, 
    ...     _environ_templates={
    ...         'IMAGE_API': '{IMAGE_PREFIX_API}/api:{VERSION_API}',
    ...         'IMAGE_PREFIX': 'should be overriden', 
    ...         'IMAGE_PREFIX_API': '{IMAGE_PREFIX}/api_repo',
    ...         'VERSION_API': lambda: 'lazy_value',
    ...     },
    ...     _post_render_funcs={
    ...         'VERSION_API': lambda value: value.replace('_', ''),
    ...     },
    ...     OverlayTestValue='unused in this test',
    ... )
    'gitlab.company.co.uk:1234/ci-testing/api_repo/api:lazyvalue'

    >>> get_env(
    ...     'PATH_HOST_API^^physical_host',
    ...     _fallback_separator='^^',
    ...     _environ={
    ...         'PATH_HOST_API': '/user/test/code/app',
    ...     },
    ... )
    '/user/test/code/app'

    >>> get_env(
    ...     'PATH_HOST_API^^physical_host',
    ...     _fallback_separator='^^',
    ...     _environ={
    ...         'PATH_HOST_API': '/user/test/code/app',
    ...         'PATH_HOST_API^^physical_host': '//c/mnt/Users/test/code/app',
    ...     },
    ... )
    '//c/mnt/Users/test/code/app'

    """
    assert hasattr(_environ, '__getitem__'), 'os.environ should be dict-like'

    keys = key.split(_fallback_separator)
    if len(keys) == 1:
        key = keys[0]
    elif len(keys) == 2:
        keys = [key, keys[0]]
    else:
        raise Exception('too many splits')

    _exception = None
    for key in keys:
        try:
            if key in kwargs:
                return kwargs[key]
            if key in _environ:
                return _environ[key]
            assert key in _environ_templates, f'unknown environ key: {key}'
            value = _environ_templates[key]
            if callable(value):
                _return = value()
            elif isinstance(value, str):
                _return = _render_env(value, partial(get_env, _environ=_environ, _environ_templates=_environ_templates, _post_render_funcs=_post_render_funcs, _fallback_separator=_fallback_separator))
            else:
                raise Exception(f'_environ_templates[{key}] is not processable')
            _return = _post_render_funcs.get(key, lambda x: x)(_return)
            _environ[key] = _return
            return _return
        except Exception as ex:
            _exception = ex
    raise _exception
