import math
import colorsys  # no support for OKLab
import codecs

from typing import NamedTuple, Self
from annotated_types import Len

from .limit import limit

type bytesRGBColor = Annotated[bytes, Len(min_length=3, max_length=3)]

class RGBColor(NamedTuple):
    r: float
    g: float
    b: float

    @classmethod
    def fromBytes(cls, rgb: bytesRGBColor) -> Self:
        return cls(*map(lambda x: x/255, rgb))

class RGBAColor(RGBColor):
    a: float


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


#from math import sqrt,cos,sin,radians
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
        cosA = math.cos(math.radians(degrees))
        sinA = math.sin(math.radians(degrees))
        self.matrix[0][0] = cosA + (1.0 - cosA) / 3.0
        self.matrix[0][1] = 1./3. * (1.0 - cosA) - math.sqrt(1./3.) * sinA
        self.matrix[0][2] = 1./3. * (1.0 - cosA) + math.sqrt(1./3.) * sinA
        self.matrix[1][0] = 1./3. * (1.0 - cosA) + math.sqrt(1./3.) * sinA
        self.matrix[1][1] = cosA + 1./3.*(1.0 - cosA)
        self.matrix[1][2] = 1./3. * (1.0 - cosA) - math.sqrt(1./3.) * sinA
        self.matrix[2][0] = 1./3. * (1.0 - cosA) - math.sqrt(1./3.) * sinA
        self.matrix[2][1] = 1./3. * (1.0 - cosA) + math.sqrt(1./3.) * sinA
        self.matrix[2][2] = cosA + 1./3. * (1.0 - cosA)
    def apply(self, r, g, b):
        rx = r * self.matrix[0][0] + g * self.matrix[0][1] + b * self.matrix[0][2]
        gx = r * self.matrix[1][0] + g * self.matrix[1][1] + b * self.matrix[1][2]
        bx = r * self.matrix[2][0] + g * self.matrix[2][1] + b * self.matrix[2][2]
        return self.clamp(rx), self.clamp(gx), self.clamp(bx)


from typing import Annotated, NamedTuple, Self


class OKLabColor(NamedTuple):
    # https://github.com/Kalabasa/leanrada.com/blob/fb0dea1db046fa083356824129b2e30f67495df0/main/scripts/update/lib/color/convert.mjs#L4
    L: float
    a: float
    b: float

    @staticmethod
    def gamma(x: float) -> float:
        return 1.055 * pow(x, 1 / 2.4) - 0.055 if x >= 0.0031308 else 12.92 * x
    @staticmethod
    def gamma_inv(x: float) -> float:
        return pow((x + 0.055) / 1.055, 2.4) if x >= 0.04045 else x / 12.92

    @classmethod
    def rgbToOkLab(cls, rgb: RGBColor) -> Self:
        r = cls.gamma_inv(rgb.r)
        g = cls.gamma_inv(rgb.g)
        b = cls.gamma_inv(rgb.b)
        l = math.cbrt(0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b)
        m = math.cbrt(0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b)
        s = math.cbrt(0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b)
        return cls(
            L= l * +0.2104542553 + m * +0.793617785 + s * -0.0040720468,
            a= l * +1.9779984951 + m * -2.428592205 + s * +0.4505937099,
            b= l * +0.0259040371 + m * +0.7827717662 + s * -0.808675766,
        )

    def oklabToRGB(self) -> RGBColor:
        l = (self.L + 0.3963377774 * self.a + 0.2158037573 * self.b) ** 3
        m = (self.L - 0.1055613458 * self.a - 0.0638541728 * self.b) ** 3
        s = (self.L - 0.0894841775 * self.a - 1.291485548 * self.b) ** 3
        return RGBColor(
            r= 255 * self.gamma(+4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s),
            g= 255 * self.gamma(-1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s),
            b= 255 * self.gamma(-0.0041960863 * l - 0.7034186147 * m + 1.707614701 * s),
        )
