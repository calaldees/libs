from functools import reduce


def parse_py(filehandle):
    import sys
    import importlib
    from pathlib import Path
    path = Path(filehandle.name)
    sys.path.append(str(path.parent))
    module = importlib.import_module(path.stem)
    return {k: v for k, v in vars(module).items() if not k.startswith('_')}


def parse_env(filehandle):
    """
    >>> from io import StringIO
    >>> input = StringIO()
    >>> _ = input.write('#comment1  \\na=1\\nb=2\\n #comment2\\n')
    >>> _ = input.seek(0)
    >>> parse_env(input)
    {'a': '1', 'b': '2'}
    """
    def _parse_env_line(acc, line):
        line = line.lstrip()
        if not line.startswith('#'):
            line_split = line.split('=', maxsplit=1)
            if len(line_split) == 2:
                key, value = line_split
                acc[key] = value
        return acc
    return reduce(_parse_env_line, filehandle.read().split('\n'), {})