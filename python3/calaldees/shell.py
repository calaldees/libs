import subprocess
import collections

import logging
log = logging.getLogger(__name__)


def cmd_args(*args, FLAG_PREFIX='--', SORT_KWARGS=False, **kwargs):
    """
    >>> cmd_args('cmd', '--flag')
    ('cmd', '--flag')
    >>> cmd_args('cmd', '--flag')
    ('cmd', '--flag')
    >>> cmd_args('cmd', flag=None, FLAG_PREFIX='-')
    ('cmd', '-flag')
    >>> cmd_args('cmd', 'arg1', flag=None, value='1', value2=2, value3=False)
    ('cmd', 'arg1', '--flag', '--value', '1', '--value2', '2', '--value3', 'False')
    >>> cmd_args('cmd', flag2=None, flag1=None, SORT_KWARGS=True)
    ('cmd', '--flag1', '--flag2')
    """
    func_sort = sorted if SORT_KWARGS else lambda arg: arg
    def format_arg(k, v):
        arg = []
        if k:
            arg.append('{FLAG_PREFIX}{k}'.format(FLAG_PREFIX=FLAG_PREFIX, k=k))  # TODO: replace with formatstring
        if v != None:
            arg.append(str(v))
        return arg
    return tuple(args) + tuple(x for k in func_sort(kwargs.keys()) for x in format_arg(k, kwargs[k]))


CommandResult = collections.namedtuple('CommandResult', ('success', 'result'))
def run_shell(*args, _RUN=subprocess.run, _TIMEOUT_SECONDS=None, **kwargs):
    cmd = cmd_args(*args, **kwargs)
    log.debug(cmd)
    cmd_result = _RUN(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=_TIMEOUT_SECONDS)
    if cmd_result.returncode != 0:
        log.error(cmd_result)
    return CommandResult(cmd_result.returncode == 0, cmd_result)

