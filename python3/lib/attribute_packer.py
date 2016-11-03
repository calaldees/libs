import struct
from collections import namedtuple


class BasePackerMixin(object):
    pass


class AttributePackerMixin(BasePackerMixin):
    Attribute = namedtuple('Attribute', ('name', 'type'))
    AttributeEncoder = namedtuple('AttributeEncoder', ('encode', 'decode', 'fmt'))
    AttributeEncoders = {
        'byte': AttributeEncoder(
            lambda value: value,
            lambda value: value,
            'B',
        ),
        'onebyte': AttributeEncoder(
            lambda value: int(value * 255),
            lambda value: value / 255,
            'B',
        ),
        'plusminusonebyte': AttributeEncoder(
            lambda value: int(((value + 1)/2) * 255),
            lambda value: ((value / 255) * 2) - 1,
            'B',
        ),

    }

    def __init__(self, attributes, assert_attributes_exist=True):
        r"""
        This can be called multiple times

        >>> class tt(AttributePackerMixin):
        ...     def __init__(self):
        ...         self.a = 0
        ...         self.b = 0
        ...         AttributePackerMixin.__init__(self, (
        ...             AttributePackerMixin.Attribute('a', 'byte'),
        ...             AttributePackerMixin.Attribute('b', 'onebyte'),
        ...         ))
        >>> obj = tt()
        >>> obj.pack_size
        2

        """
        if assert_attributes_exist:
            for attribute in attributes:
                assert hasattr(self, attribute.name), """object '{}' should have the required attribute '{}'""".format(self, attribute.name)
        if not hasattr(self, '_pack_attributes'):
            self._pack_attributes = tuple()
        self._pack_attributes += attributes
        self.pack_size = sum(struct.calcsize(self.AttributeEncoders[attribute.type].fmt) for attribute in self._pack_attributes)

    def pack(self, buffer, offset):
        r"""
        >>> class tt(AttributePackerMixin):
        ...     def __init__(self):
        ...         self.a = 16
        ...         self.b = 0.5
        ...         AttributePackerMixin.__init__(self, (
        ...             AttributePackerMixin.Attribute('a', 'byte'),
        ...             AttributePackerMixin.Attribute('b', 'onebyte'),
        ...         ))
        >>> obj = tt()
        >>> buffer = bytearray(b'\x01\x02\x03\x04')
        >>> obj.pack(buffer, 1)
        3
        >>> buffer
        bytearray(b'\x01\x10\x7f\x04')

        """
        for value, encoder in (
                (getattr(self, attribute_name), self.AttributeEncoders[attribute_type])
                for attribute_name, attribute_type in self._pack_attributes
        ):
            struct.pack_into(encoder.fmt, buffer, offset, encoder.encode(value))
            offset += struct.calcsize(encoder.fmt)
        return offset

    def unpack(self, buffer, offset):
        r"""
        >>> class tt(AttributePackerMixin):
        ...     def __init__(self):
        ...         self.a = 0
        ...         self.b = 0
        ...         AttributePackerMixin.__init__(self, (
        ...             AttributePackerMixin.Attribute('a', 'byte'),
        ...             AttributePackerMixin.Attribute('b', 'onebyte'),
        ...         ))
        >>> obj = tt()
        >>> buffer = bytearray(b'\x01\xff\x7f\x04')
        >>> obj.unpack(buffer, 1)
        3
        >>> obj.a
        255
        >>> assert (obj.b - 0.5) < 0.01

        """
        for attribute_name, encoder in (
                (attribute_name, self.AttributeEncoders[attribute_type])
                for attribute_name, attribute_type in self._pack_attributes
        ):
            value, = struct.unpack_from(encoder.fmt, buffer, offset)
            offset += struct.calcsize(encoder.fmt)
            setattr(self, attribute_name, encoder.decode(value))
        return offset


class CollectionPackerMixin(BasePackerMixin):
    """
    Mixin for parent object that stores an iterable of items that support AttributePackerMixin
    This provides the same interface as a single AttributePackerMixin
    """
    def __init__(self, pack_collection):
        self._pack_collection = pack_collection

    @property
    def pack_size(self):
        r"""
        >>> class TestItem(AttributePackerMixin):
        ...     def __init__(self):
        ...         self.a = 0
        ...         self.b = 0
        ...         AttributePackerMixin.__init__(self, (
        ...             AttributePackerMixin.Attribute('a', 'byte'),
        ...             AttributePackerMixin.Attribute('b', 'onebyte'),
        ...         ))
        >>> TestItem().pack_size
        2
        >>> class TestCollection(CollectionPackerMixin):
        ...     def __init__(self):
        ...         self.collection = (TestItem(), TestItem())
        ...         CollectionPackerMixin.__init__(self, self.collection)
        >>> TestCollection().pack_size
        4
        """
        return sum((item.pack_size for item in self._pack_collection))

    def pack(self, buffer, offset):
        for item in self._pack_collection:
            offset += item.pack(buffer, offset)
        return offset

    def unpack(self, buffer, offset):
        for item in self._pack_collection:
            offset += item.unpack(buffer, offset)
