from Crypto.Cipher import AES
import base64
import os
import json

# Inspied by
#  http://sentdex.com/sentiment-analysisbig-data-and-python-tutorials-algorithmic-trading/encryption-and-decryption-in-python-code-example-with-explanation/

# the block size for cipher obj, can be 16 24 or 32. 16 matches 128 bit.
#32 bytes = 256 bits
#16 = 128 bits
BLOCK_SIZE = 16

# the character used for padding - used to ensure that your value is always a multiple of BLOCK_SIZE
PADDING = '|'

DEFAULT_METHOD = AES

def _pad(data, block_size=BLOCK_SIZE, padding=PADDING):
    if isinstance(data, bytes):  # ensure we can pad bytes or strings by making padding match the data type
        padding = padding.encode('utf-8')
    return data + (block_size - len(data) % block_size) * padding

def encrypt(data, secret=None, method=DEFAULT_METHOD, block_size=BLOCK_SIZE, padding=PADDING):
    """
    Encrypt a python datastructure with a key as a base 64 string
    >>> data = {'a': [1, 2, 3]}
    >>> encrypt(data, 'password')
    b'7HXC5jodYm6SSS7gFSGyM/Dqj6i16sgBbrMt6fenJ6c='
    """
    if not secret:
        secret = os.urandom(block_size)
    secret = _pad(secret, block_size, padding)
    return base64.b64encode(
        method.new(secret).encrypt(
            _pad(
                json.dumps(data),
                block_size, padding
            ).encode('utf-8')
        )
    )

def decrypt(data, secret, method=DEFAULT_METHOD, block_size=BLOCK_SIZE, padding=PADDING):
    """
    Decrypt an encrypted base 64 string into a python datastructure using a key
    >>> data = b'7HXC5jodYm6SSS7gFSGyM/Dqj6i16sgBbrMt6fenJ6c='
    >>> decrypt(data, 'password')
    {'a': [1, 2, 3]}
    """
    secret = _pad(secret, block_size, padding)
    return json.loads(
        method.new(secret).decrypt(
            base64.b64decode(data)
        ).decode('utf-8').rstrip(padding)
    )
