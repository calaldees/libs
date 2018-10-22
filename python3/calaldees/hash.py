import zlib
import hashlib


def hash_files(files, hasher=zlib.adler32):
    """
    adler32 is a good-enough checksum that's fast to compute.
    """
    return "%X" % abs(hash(frozenset(hasher(open(_file, 'rb').read()) for _file in files)))


def hash_data(data, hasher=hashlib.sha256):
    hasher = hasher()
    hasher.update(str(data).encode())
    return hasher.hexdigest()

