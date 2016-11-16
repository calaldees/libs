import struct
from collections import namedtuple
import os.path
import tempfile

import logging
log = logging.getLogger(__name__)

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

        >>> obj = _TestAttributePacker()
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
        >>> obj = _TestAttributePacker(16, 0.5)
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
        >>> obj = _TestAttributePacker()
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
        r"""
        >>> _TestAttributePacker().pack_size
        2
        >>> _TestPackerCollection((_TestAttributePacker(), _TestAttributePacker())).pack_size
        4
        """
        assert isinstance(pack_collection, tuple), 'packable_collections must be an immutable `tuple`'
        for item in pack_collection:
            assert isinstance(item, BasePackerMixin), 'packable_collections must contain only `packable` items'
        self._pack_collection = pack_collection
        self._pack_size = sum((item.pack_size for item in self._pack_collection))

    @property
    def pack_size(self):
        return self._pack_size

    def pack(self, buffer, offset):
        for item in self._pack_collection:
            offset = item.pack(buffer, offset)
        return offset

    def unpack(self, buffer, offset):
        for item in self._pack_collection:
            offset = item.unpack(buffer, offset)
        return offset


# Frame Persistence ------------------------------------------------------------

class BaseFramePacker(object):
    FrameDetails = namedtuple('FrameDetails', ('number', 'pos', 'size'))

    def __init__(self, pack_collection):
        assert isinstance(pack_collection, BasePackerMixin)
        self._top_level_packer_collection = pack_collection
        self.frame_size = pack_collection.pack_size
        self.current_frame = 0

    def _get_frame_details(self, frame_number=None):
        frame_number = frame_number if frame_number is not None else self.current_frame
        frame = self.FrameDetails(
            number=frame_number,
            pos=frame_number * self.frame_size,
            size=self.frame_size,
        )
        self.current_frame = frame.number + 1
        return frame

    def _get_byte_size(self):
        """Override"""
        return 0

    @property
    def frames(self):
        return self._get_byte_size() // self.frame_size

    def save_frame(self):
        pass

    def restore_frame(self):
        pass

    def close(self):
        pass

    # TODO: make this a context manager to call close?


class MemoryFramePacker(BaseFramePacker):
    def __init__(self, packer_collection):
        super().__init__(packer_collection)
        self._buffer = bytearray()

    def _get_byte_size(self):
        return len(self._buffer)

    def save_frame(self, frame_number=None, insert=True):
        r"""
        >>> obj1 = _TestAttributePacker()
        >>> obj2 = _TestAttributePacker()
        >>> mp = MemoryFramePacker(_TestPackerCollection((obj1, obj2)))
        >>> mp.save_frame()
        >>> obj1.a = 16
        >>> obj1.b = 0.5
        >>> obj2.a = 24
        >>> obj2.b = 0
        >>> mp.save_frame()
        >>> mp._buffer
        bytearray(b'\x00\x00\x00\x00\x10\x7f\x18\x00')
        """
        frame = self._get_frame_details(frame_number)
        if insert:
            self._buffer[frame.pos:frame.pos] += bytearray(frame.size)
        offset = self._top_level_packer_collection.pack(self._buffer, frame.pos)
        assert offset - frame.pos == frame.size, 'Should have written the exact frame.size of bytes'

    def restore_frame(self, frame_number=None):
        r"""
        >>> obj1 = _TestAttributePacker()
        >>> obj2 = _TestAttributePacker()
        >>> mp = MemoryFramePacker(_TestPackerCollection((obj1, obj2)))
        >>> mp._buffer = bytearray(b'\x00\x00\x00\x00' + b'\x10\x7f' + b'\x18\x00')
        >>> mp.restore_frame(1)
        >>> obj1.a
        16
        >>> obj2.a
        24
        """
        frame = self._get_frame_details(frame_number)
        offset = self._top_level_packer_collection.unpack(self._buffer, frame.pos)
        assert offset - frame.pos == frame.size, 'Should have read the exact frame.size of bytes'

    def close(self):
        self._buffer[:] = bytearray()


class PersistentFramePacker(BaseFramePacker):
    def __init__(self, packer_collection, filename=None):
        super().__init__(packer_collection)
        self.filename = filename
        if filename and os.path.exists(filename):
            self._byte_size = os.stat(filename).st_size
            log.debug(f'Attach to existing packer with {self.frames} frames')
        self._handler = None
        self._buffer = bytearray(self.frame_size)

    def _get_byte_size(self):
        return self._byte_size

    @property
    def handler(self):
        if not self._handler:
            if self.filename:
                log.debug(f'Open {self.filename}')
                self._handler = open(self.filename, 'r+b' if os.path.exists(self.filename) else 'w+b')
            else:
                log.debug(f'Open [tempfile]')
                self._handler = tempfile.TemporaryFile(mode='w+b')
        return self._handler

    def close(self):
        if self._handler:
            self._handler.close()
            self._handler = None

    def save_frame(self, frame_number=None):
        frame = self._get_frame_details(frame_number)
        self.handler.seek(frame.pos)
        self._top_level_packer_collection.pack(self._buffer, 0)
        self.handler.write(self._buffer)

    def restore_frame(self, frame_number=None):
        frame = self._get_frame_details(frame_number)
        self.handler.seek(frame.pos)
        self._top_level_packer_collection.unpack(self.handler.read(frame.size), 0)


# Test Utils -------------------------------------------------------------------

class _TestAttributePacker(AttributePackerMixin):
    def __init__(self, a=0, b=0):
        self.a = a
        self.b = b
        AttributePackerMixin.__init__(self, (
            AttributePackerMixin.Attribute('a', 'byte'),
            AttributePackerMixin.Attribute('b', 'onebyte'),
        ))

class _TestPackerCollection(CollectionPackerMixin):
    def __init__(self, collection):
        self.collection = collection
        CollectionPackerMixin.__init__(self, self.collection)
