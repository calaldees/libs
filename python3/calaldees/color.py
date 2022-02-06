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


from math import sqrt,cos,sin,radians
class RGBRotate(object):
    """
    https://stackoverflow.com/a/8510751/3356840
    Matrix Operations for Image Processing - Paul Haeberli Nov 1993
    http://www.graficaobscura.com/matrix/index.html
    >>> RGBRotate(0).apply(255,0,0)
    (255, 0, 0)
    >>> RGBRotate(360).apply(255,0,0)
    (255, 0, 0)
    >>> RGBRotate(120).apply(255,0,0)
    (0, 255, 0)
    """
    @staticmethod
    def clamp(v):
        if v < 0:
            return 0
        if v > 255:
            return 255
        return int(v + 0.5)
    def __init__(self, degrees):
        self.matrix = [[1,0,0],[0,1,0],[0,0,1]]
        self.set_hue_rotation(degrees)
    def set_hue_rotation(self, degrees):
        cosA = cos(radians(degrees))
        sinA = sin(radians(degrees))
        self.matrix[0][0] = cosA + (1.0 - cosA) / 3.0
        self.matrix[0][1] = 1./3. * (1.0 - cosA) - sqrt(1./3.) * sinA
        self.matrix[0][2] = 1./3. * (1.0 - cosA) + sqrt(1./3.) * sinA
        self.matrix[1][0] = 1./3. * (1.0 - cosA) + sqrt(1./3.) * sinA
        self.matrix[1][1] = cosA + 1./3.*(1.0 - cosA)
        self.matrix[1][2] = 1./3. * (1.0 - cosA) - sqrt(1./3.) * sinA
        self.matrix[2][0] = 1./3. * (1.0 - cosA) - sqrt(1./3.) * sinA
        self.matrix[2][1] = 1./3. * (1.0 - cosA) + sqrt(1./3.) * sinA
        self.matrix[2][2] = cosA + 1./3. * (1.0 - cosA)
    def apply(self, r, g, b):
        rx = r * self.matrix[0][0] + g * self.matrix[0][1] + b * self.matrix[0][2]
        gx = r * self.matrix[1][0] + g * self.matrix[1][1] + b * self.matrix[1][2]
        bx = r * self.matrix[2][0] + g * self.matrix[2][1] + b * self.matrix[2][2]
        return self.clamp(rx), self.clamp(gx), self.clamp(bx)
