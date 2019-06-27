DESCRIPTION="""
AutoIncrement
"""

import os.path
import re

# Reference to 'lookahead' example https://stackoverflow.com/a/45683049/3356840
DEFAULT_REGEX = re.compile(r"""(?<=version=')(\d+)""")

def auto_increment(data, regex=DEFAULT_REGEX):
    """
    >>> auto_increment('''xXx version='12' xXx''')
    "xXx version='13' xXx"
    """
    return regex.sub(lambda match: str(int(match.group(1)) + 1), data)


# Main - file handling ---------------------------------------------------------

def _read(filename):
    assert os.path.isfile(filename)
    with open(filename, 'rt') as filehandle:
        return filehandle.read()

def _write(filename, data):
    with open(filename, 'wt') as filehandle:
        return filehandle.write(data)

def main(filename='', regex=DEFAULT_REGEX):
    _write(filename, auto_increment(_read(filename), regex))


# Commandline ------------------------------------------------------------------

def get_args():
    import argparse

    parser = argparse.ArgumentParser(
        prog=__name__,
        description=DESCRIPTION,
    )

    parser.add_argument('filename', action='store', help='filename')
    parser.add_argument('--regex', type=re.compile, help=f'regex', default=DEFAULT_REGEX)

    args = parser.parse_args()
    return vars(args)


if __name__ == "__main__":
    kwargs = get_args()
    main(**kwargs)
