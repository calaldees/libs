
def postmortem(func, *args, **kwargs):
    import traceback
    import pdb
    import sys
    try:
        return func(*args, **kwargs)
    except Exception:
        type, value, tb = sys.exc_info()
        traceback.print_exc()
        pdb.post_mortem(tb)


def init_vscode_debuger(secret="my_secret", address=('0.0.0.0', 3000), wait_for_attach=False):
    import ptvsd
    ptvsd.enable_attach(secret, address=address)
    if wait_for_attach:
        ptvsd.wait_for_attach()
