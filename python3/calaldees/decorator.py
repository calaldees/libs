
# Reference - http://stackoverflow.com/questions/2182858/how-can-i-pack-serveral-decorators-into-one
def decorator_combine(*dec_funs):
    def _inner_chain(f):
        for dec in reversed(dec_funs):
            f = dec(f)
        return f
    return _inner_chain
