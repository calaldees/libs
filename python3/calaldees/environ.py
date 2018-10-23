from os import environ
import re


def get_env(key, _environ=environ, _environ_templates={}):
    """
    >>> get_env(
    ...    'IMAGE_API', 
    ...    _environ={
    ...        'IMAGE_PREFIX': 'gitlab.company.co.uk:1234/ci-testing',
    ...     }, 
    ...     _environ_templates={
    ...         'IMAGE_API': '{IMAGE_PREFIX_API}/api:{VERSION_API}',
    ...         'IMAGE_PREFIX': 'should be overriden', 
    ...         'IMAGE_PREFIX_API': '{IMAGE_PREFIX}/api_repo',
    ...         'VERSION_API': lambda: 'lazy_value',
    ...     },
    ... )
    'gitlab.company.co.uk:1234/ci-testing/api_repo/api:lazy_value'
    """
    assert _environ, 'os.environ should be passed'
    if key in _environ:
        return _environ[key]
    assert key in _environ_templates, 'unknown ENV'
    value = _environ_templates[key]
    if callable(value):
        _return = value()
    elif isinstance(value, str):
        value_sub_keys = tuple(match.group(1) for match in re.finditer(r'{(.*?)}', value))
        _return = value.format(**{
            value_sub_key: get_env(value_sub_key, _environ=_environ, _environ_templates=_environ_templates)
            for value_sub_key in value_sub_keys
        })
    else:
        raise Exception(f'_environ_templates[{key}] is not processable')
    _environ[key] = _return
    return _return
