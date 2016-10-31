import struct
from collections import namedtuple


class AttributePackerMixin(object):
    _ValueEncoderPair = namedtuple('ValueEncoderPair', ('value', 'encoder'))
    Attribute = namedtuple('Attribute', ('name', 'type'))
    AttributeEncoder = namedtuple('AttributeEncoder', ('encode', 'decode', 'fmt'))
    AttributeEncoders = {
        'byte': AttributeEncoder(
            lambda value: value,
            lambda value: value,
            'B',
        ),
        'one': AttributeEncoder(
            lambda value: value * 255,
            lambda value: value / 255,
            'B',
        ),
    }

    def __init__(self, attributes):
        self.attributes = attributes

    def pack(self, buffer=None, offset=None):
        for value, encoder in (
                self._ValueEncoderPair(
                    value=getattr(self, attribute_name),
                    encoder=self.AttributeEncoders[attribute_type],
                )
                for attribute_name, attribute_type in self.attributes
        ):
            struct.pack_into(encoder.fmt, buffer, offset, value)
            #offset += struct.calcsize(encoder.fmt)
        #return offset

    def unpack(self, data=None, buffer=None, offset=None):
        raise NotImplementedError()
