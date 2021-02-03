from typing import NamedTuple

class Position(NamedTuple):
    x: int
    y: int
    z: int

class Dimension(NamedTuple):
    width: int
    height: int
    depth: int

    @property  # TODO: lazy/cached?
    def size(self):
        return self.width * self.height * self.depth

    def normalise_position(self, position):
        """
        Wrap co-ordinates that are out of bounds to inbounds
        """
        return Position(
            position.x % self.width,
            position.y % self.height,
            position.z % self.depth,
        )

    def index_to_position(self, i):
        """
        >>> Dimension(8, 8, 3).index_to_position(0)
        Position(x=0, y=0, z=0)
        >>> Dimension(8, 8, 3).index_to_position(7)
        Position(x=7, y=0, z=0)
        >>> Dimension(8, 8, 3).index_to_position(8)
        Position(x=0, y=1, z=0)
        >>> Dimension(8, 8, 3).index_to_position(64)
        Position(x=0, y=0, z=1)
        >>> Dimension(8, 8, 3).index_to_position(73)
        Position(x=1, y=1, z=1)
        >>> Dimension(8, 8, 3).index_to_position(146)
        Position(x=2, y=2, z=2)
        >>> Dimension(4, 8, 2,).index_to_position(46)
        Position(x=2, y=3, z=1)
        >>> Dimension(4, 8, 2,).index_to_position(63)
        Position(x=3, y=7, z=1)
        """
        return Position(
            i % self.width,
            i//self.width % self.height,
            i//(self.width * self.height),
        )

    def position_to_index(self, position):
        """
        inverse of `position_to_index`

        >>> Dimension(8, 8, 3).position_to_index(Position(0, 0, 0))
h        0
        >>> Dimension(8, 8, 3).position_to_index(Position(7, 0, 0))
        7
        >>> Dimension(8, 8, 3).position_to_index(Position(0, 1, 0))
        8
        >>> Dimension(8, 8, 3).position_to_index(Position(0, 0, 1))
        64
        >>> Dimension(8, 8, 3).position_to_index(Position(1, 1, 1))
        73
        >>> Dimension(8, 8, 3).position_to_index(Position(2, 2, 2))
        146
        >>> Dimension(4, 8, 2).position_to_index(Position(2, 3, 1))
        46
        >>> Dimension(4, 8, 2).position_to_index(Position(3, 7, 1))
        63

        wrap edges
        0 1 2   9 10 11  18 19 20
        3 4 5  12 13 14  21 22 23
        6 7 8  15 16 17  24 25 26

        >>> Dimension(3, 3, 3).position_to_index(Position(-1, 0, 0))
        2
        >>> Dimension(3, 3, 3).position_to_index(Position(-2, 0, 0))
        1
        >>> Dimension(3, 3, 3).position_to_index(Position(-3, 0, 0))
        0
        >>> Dimension(3, 3, 3).position_to_index(Position(-4, 0, 0))
        2
        >>> Dimension(3, 3, 3).position_to_index(Position(0, -1, 0))
        6
        >>> Dimension(3, 3, 3).position_to_index(Position(-1, -1, 0))
        8
        >>> Dimension(3, 3, 3).position_to_index(Position(0, 0, -1))
        18
        >>> Dimension(3, 3, 3).position_to_index(Position(-1, -1, -1))
        26
        >>> Dimension(3, 3, 3).position_to_index(Position(-2, -2, -2))
        13
        >>> Dimension(3, 3, 3).position_to_index(Position(1, 1, 1))
        13
        >>> Dimension(3, 3, 3).position_to_index(Position(3, 3, 0))
        0
        """
        _position = self.normalise_position(position)
        return (self.width * self.height * _position.z) + (self.width * _position.y) + _position.x


class Array():
    def __init__(self, dimension, data):
        """
        Unfinished wrapper

        >>> aa = Array(Dimension(3, 3, 3), tuple(range(3*3*3)))
        >>> aa.get(Position(1,1,1))
        13
        """
        assert isinstance(dimension, Dimension)
        assert len(data) ==  dimension.size, f"{dimension.size=} does not match data size {len(data)}"
        self.dimension = dimension
        self.data = data
    def get(self, position):
        return self.data[self.dimension.position_to_index(position)]
