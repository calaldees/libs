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


def get_env(key, _environ=environ, _environ_templates={}, **kwargs):
    """
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
    ...     OverlayTestValue='unused in this test',
    ... )
    'gitlab.company.co.uk:1234/ci-testing/api_repo/api:lazy_value'
    """
    assert _environ, 'os.environ should be passed'
    if key in kwargs:
        return kwargs[key]
    if key in _environ:
        return _environ[key]
    assert key in _environ_templates, f'unknown environ key: {key}'
    value = _environ_templates[key]
    if callable(value):
        _return = value()
    elif isinstance(value, str):
        _return = _render_env(value, partial(get_env, _environ=_environ, _environ_templates=_environ_templates))
    else:
        raise Exception(f'_environ_templates[{key}] is not processable')
    _environ[key] = _return
    return _return
