import colorsys
import codecs

from .limit import limit


def parse_rgb_color(color, fallback_color=(0.0, 0.0, 0.0)):
    """
    Normalise a range of string values into (r,g,b) tuple from 0 to 1

    >>> parse_rgb_color('what is this?')
    (0.0, 0.0, 0.0)
    >>> parse_rgb_color((1,1,1))
    (1.0, 1.0, 1.0)
    >>> parse_rgb_color([0,0.5,1])
    (0.0, 0.5, 1.0)
    >>> parse_rgb_color('#FFFFFF')
    (1.0, 1.0, 1.0)
    >>> parse_rgb_color('#FFFFFFFF')
    (1.0, 1.0, 1.0, 1.0)
    >>> parse_rgb_color('hsv:0,1,1')
    (1.0, 0.0, 0.0)
    >>> parse_rgb_color('hls:0,1,1')
    (1.0, 1.0, 1.0)
    >>> parse_rgb_color('yiq:0,0,0')
    (0.0, 0.0, 0.0)
    >>> parse_rgb_color('hsv:0,1,1,0.5')
    (1.0, 0.0, 0.0, 0.5)
    >>> parse_rgb_color('rgb:1,1,1')
    (1.0, 1.0, 1.0)
    >>> parse_rgb_color('rgb:1,1,1,1')
    (1.0, 1.0, 1.0, 1.0)
    >>> parse_rgb_color(0.5)
    (0.5, 0.5, 0.5)
    >>> parse_rgb_color(1)
    (1.0, 1.0, 1.0)
    """
    if isinstance(color, (float, int)):
        color = (color, ) * 3
    if isinstance(color, (tuple, list)):
        return tuple(map(float, color))
    if isinstance(color, str):
        if color.startswith('#'):
            return tuple(map(lambda v: limit(v/255, 0.0, 1.0), codecs.decode(color.strip('#'), "hex")))
        elif color.find(':') >= 0:
            color_type, value = color.split(':')
            values = tuple(map(float, value.split(',')))
            if color_type == 'rgb':
                return values
            return getattr(colorsys, '{0}_to_rgb'.format(color_type))(*values[0:3]) + values[3:]
    if fallback_color:
        return fallback_color
    raise AttributeError('{0} is not parseable'.format(color))


def color_distance(target, actual, threshold=20):
    """
    >>> color_distance((0,0,0), (0,0,0))
    0
    >>> color_distance((0,0,255), (1,18,255))
    19
    >>> color_distance((255,0,0), (0,0,255))
    >>> color_distance((0,0,0), (10,10,10))
    """
    distance = sum(abs(a - b) for a, b in zip(target, actual))
    return distance if distance < threshold else None


def color_close(target, actual, threshold=20):
    distance = color_distance(target, actual, threshold)
    return True if distance is not None else False
