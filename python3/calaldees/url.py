from urllib.parse import urlunparse, urlparse, urlencode


def build_url(baseurl='', path='', query_string_dict=None, scheme='', netloc='', host='', port=0, parameters='', fragment=''):
    """
    For url_part index's - refer to https://docs.python.org/2/library/urlparse.html#urlparse.urlparse
    scheme://netloc/path;parameters?query#fragment

    >>> build_url('myhostname')
    'http://localhost/myhostname'
    >>> build_url(host='myhostname')
    'http://myhostname/'
    >>> build_url(host='myhostname', port=8000)
    'http://myhostname:8000/'
    >>> build_url(host='myhostname', port=8000, query_string_dict={'a':1, 'b':2})
    'http://myhostname:8000/?a=1&b=2'
    >>> build_url(baseurl='https://drive.google.com/files')
    'https://drive.google.com/files'
    >>> build_url(baseurl='https://drive.google.com/files', path='/alternate/files')
    'https://drive.google.com/alternate/files'
    """
    return urlunparse(
        kwarg_value or baseurl_value or fallback_value
        for kwarg_value, baseurl_value, fallback_value in zip(
            (
                scheme,
                netloc if netloc else host + (':{}'.format(int(port)) if port else ''),
                path,
                parameters,
                urlencode(query_string_dict or {}),
                fragment
            ),
            urlparse(baseurl),
            (
                'http',
                'localhost',
                '/',
                '',
                '',
                '',
            )
        )
    )
