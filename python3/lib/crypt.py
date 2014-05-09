from Crypto.Cipher import AES
import base64
import os
import json


class Cryptor(object):
    """
    Encrypt/Decrypt Python data structures to/from base64 strings
    
    Inspied by
        http://sentdex.com/sentiment-analysisbig-data-and-python-tutorials-algorithmic-trading/encryption-and-decryption-in-python-code-example-with-explanation/
    The block size for cipher obj, can be 16 24 or 32.
        32 bytes = 256 bits
        16 bytes = 128 bits
    The character used for padding - used to ensure that your value is always a multiple of BLOCK_SIZE
    
    Todo:
        Add custom json serializer support
    """
    DEFAULT_METHOD = AES
    BLOCK_SIZE = 16
    PADDING = '|'
    
    def __init__(self, secret=None, method=DEFAULT_METHOD, block_size=BLOCK_SIZE, padding=PADDING):
        self.method = method
        self.block_size = block_size
        self.padding = padding
        if not secret:
            secret = os.urandom(block_size)
        self.secret = self._pad(secret)

    def _pad(self, data):
        padding = self.padding
        if isinstance(data, bytes):  # ensure we can pad bytes or strings by making padding match the data type
            padding = self.padding.encode('utf-8')
        return data + (self.block_size - len(data) % self.block_size) * padding
    
    def encrypt(self, data):
        """
        Encrypt a python datastructure with a key as a base 64 string
        >>> data = {'a': [1, 2, 3]}
        >>> Cryptor(secret='password').encrypt(data)
        b'7HXC5jodYm6SSS7gFSGyM/Dqj6i16sgBbrMt6fenJ6c='
        """
        return base64.b64encode(
            self.method.new(self.secret).encrypt(
                self._pad(
                    json.dumps(data)
                ).encode('utf-8')
            )
        )
    
    def decrypt(self, data):
        """
        Decrypt an encrypted base 64 string into a python datastructure using a key
        >>> data = b'7HXC5jodYm6SSS7gFSGyM/Dqj6i16sgBbrMt6fenJ6c='
        >>> Cryptor(secret='password').decrypt(data)
        {'a': [1, 2, 3]}
        """
        return json.loads(
            self.method.new(self.secret).decrypt(
                base64.b64decode(data)
            ).decode('utf-8').rstrip(self.padding)
        )