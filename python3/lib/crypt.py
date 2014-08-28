from Crypto.Cipher import AES
import hmac
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
        Add CBC encryption method
        Add custom json serializer support
        pbkdf2 for keygen
    """
    SIGNITURE_SIZE = 16  # hmac is 24 bytes
    BLOCK_SIZE = 16
    PADDING = '|'
    DEFAULT_METHOD = AES
    DEFAULT_METHOD_KWARGS = dict(mode=AES.MODE_CBC)

    def __init__(self, secret, block_size=BLOCK_SIZE, padding=PADDING, method=DEFAULT_METHOD, method_kwargs=DEFAULT_METHOD_KWARGS, iv=None):
        """
        secret: should be bytes and as long as possible (will accept strings)
        """
        assert secret, 'A secret key is required'
        self.block_size = block_size
        self.padding = padding
        self.method = method
        self.method_kwargs = method_kwargs
        if isinstance(secret, str):
            secret = secret.encode('utf-8')
        self.secret_signiture = self._pad(secret[:len(secret)//2])
        self.secret_message = self._pad(secret[len(secret)//2:])
        self.iv = iv if iv else os.urandom(block_size)
        self.method_kwargs['IV'] = iv

    def _pad(self, data):
        padding = self.padding
        if isinstance(data, bytes):  # ensure we can pad bytes or strings by making padding match the data type
            padding = self.padding.encode('utf-8')
        return data + (self.block_size - len(data) % self.block_size) * padding

    def encrypt(self, data):
        """
        Encrypt a python datastructure with a key as a base 64 string
        The first 24 characters of the output will be an hmac signiture
        >>> data = {'a': [1, 2, 3]}
        >>> Cryptor(secret='password', iv=b'1'*16).encrypt(data)
        b'IZYmd2E81RengaMT804WsDExMTExMTExMTExMTExMTEEeNyxU69k28VEyGKw8dLpMe3EPfJv81UGbNEK6iBZgw=='
        """
        msg = self.method.new(key=self.secret_message, **self.method_kwargs).encrypt(
            self._pad(
                json.dumps(data)
            ).encode('utf-8')
        )
        signiture = hmac.new(self.secret_signiture, msg).digest()
        return base64.b64encode(signiture + self.iv + msg)

    def decrypt(self, data):
        """
        Decrypt an encrypted base 64 string into a python datastructure using a key
        The first 24 characters of the input will be an hmac signiture
        The next 'block_size' of bytes could be an IV (if one was used at setup)
        >>> data = b'IZYmd2E81RengaMT804WsDExMTExMTExMTExMTExMTEEeNyxU69k28VEyGKw8dLpMe3EPfJv81UGbNEK6iBZgw=='
        >>> Cryptor(secret='password').decrypt(data)
        {'a': [1, 2, 3]}
        """
        data = base64.b64decode(data)
        signiture = data[:self.SIGNITURE_SIZE]
        self.method_kwargs['IV'] = data[self.SIGNITURE_SIZE: self.SIGNITURE_SIZE + self.block_size]
        msg = data[self.SIGNITURE_SIZE + self.block_size:]
        if not hmac.compare_digest(signiture, hmac.new(self.secret_signiture, msg).digest()):
            raise Exception('Signiture not valid. We did not generate the encrypted message.')
        return json.loads(
            self.method.new(key=self.secret_message, **self.method_kwargs).decrypt(
                msg
            ).decode('utf-8').rstrip(self.padding)
        )
