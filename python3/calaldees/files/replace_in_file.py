import re


def replace_in_file(filename, pattern, replacement):
    r"""
    >>> import tempfile
    >>> tempdir = tempfile.TemporaryDirectory()
    >>> filename = f'{tempdir.name}/test.txt'
    >>> with open(filename, 'w') as filehandle:
    ...     filehandle.write('''
    ...         value=1
    ...         another=2
    ...     ''')
    39
    >>> replace_in_file(filename, r'(?<=value=)(\d+)', '30')
    >>> with open(filename, mode='r') as filehandle:
    ...     filehandle.read().strip().replace(' ', '')
    'value=30\nanother=2'
    >>> tempdir.cleanup()
    """
    if isinstance(pattern, str):
        pattern = re.compile(pattern)
    with open(filename, mode='r', encoding='utf-8') as filehandle:
        data = filehandle.read()
    data = pattern.sub(replacement, data)
    with open(filename, mode='w', encoding='utf-8') as filehandle:
        filehandle.write(data)
