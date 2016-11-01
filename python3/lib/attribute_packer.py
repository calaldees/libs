import struct
from collections import namedtuple


class AttributePackerMixin(object):
    Attribute = namedtuple('Attribute', ('name', 'type'))
    AttributeEncoder = namedtuple('AttributeEncoder', ('encode', 'decode', 'fmt'))
    AttributeEncoders = {
        'byte': AttributeEncoder(
            lambda value: value,
            lambda value: value,
            'B',
        ),
        'onebyte': AttributeEncoder(
            lambda value: value * 255,
            lambda value: value / 255,
            'B',
        ),
    }

    def __init__(self, attributes):
        self.attributes = attributes

    def pack(self, buffer=None, offset=None):
        """
        >>> class tt(AttributePackerMixin):
        ...     def __init__(self):
        ...         AttributePackerMixin.__init__(self, (
        ...             AttributePackerMixin.Attribute('a', 'byte'),
        ...             AttributePackerMixin.Attribute('b', 'onebyte'),
        ...         ))
        ...         self.a = 10
        ...         self.b = 0.5
        >>> obj = tt()
        """
        for value, encoder in (
                (getattr(self, attribute_name), self.AttributeEncoders[attribute_type])
                for attribute_name, attribute_type in self.attributes
        ):
            struct.pack_into(encoder.fmt, buffer, offset, encoder.encode(value))
            offset += struct.calcsize(encoder.fmt)
        return offset

    def unpack(self, buffer=None, offset=None):
        for attribute_name, encoder in (
                (attribute_name, self.AttributeEncoders[attribute_type])
                for attribute_name, attribute_type in self.attributes
        ):
            value, = struct.unpack_from(encoder.fmt, buffer, offset)
            offset += struct.calcsize(encoder.fmt)
            setattr(self, attribute_name, encoder.decode(value))
        return offset
