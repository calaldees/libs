import pytest
from collections import namedtuple

from .timeline import Timeline

class Location(object):
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y


@pytest.fixture()
def tl():
    return Timeline()


@pytest.fixture()
def o1():
    return Location()


@pytest.fixture()
def o2():
    return Location()


# Tests ------------------------------------------------------------------------

def test_timeline_creation(tl):
    assert tl.duration == 0


InvalidArguemnts = namedtuple('InvalidArguments', ('args', 'kwargs'))
@pytest.mark.parametrize(('argsX', 'kwargsX'), (
    InvalidArguemnts(args=(), kwargs=dict()),
    InvalidArguemnts(args=(o1(), -1), kwargs=dict(valuesFrom={'a': 1})),
    InvalidArguemnts(args=(o1(), 0), kwargs=dict()),
))
def test_timeline_from_to_invalid(tl, argsX, kwargsX):
    with pytest.raises((AssertionError, TypeError)) as exc:
        tl.from_to(*argsX, **kwargsX)


def test_timeline_to(tl, o1):
    tl.to(o1, 10, {'x': 100})
    assert tl.duration == 10
    tl.to(o1, 10, {'y': 100})
    assert tl.duration == 20


def test_timeline_render_single(tl, o1):
    assert o1.x == 0
    assert o1.y == 0
    tl.to(o1, 10, {'x': 100}).to(o1, 10, {'y': 100})

    ren = tl.get_renderer()

    ren.render(0)
    assert o1.x == 0
    assert o1.y == 0

    ren.render(5)
    assert o1.x == 50
    assert o1.y == 0

    ren.render(10)
    assert o1.x == 100
    assert o1.y == 0

    ren.render(15)
    assert o1.x == 100
    assert o1.y == 50

    ren.render(20)
    assert o1.x == 100
    assert o1.y == 100


def test_timeline_render_multiple_elements(tl, o1, o2):
    tl.to((o1, o2), 10, {'x': 100})

    ren = tl.get_renderer()

    ren.render(0)
    assert o1.x == 0
    assert o1.y == 0
    assert o2.x == 0
    assert o2.y == 0

    ren.render(5)
    assert o1.x == 50
    assert o1.y == 0
    assert o2.x == 50
    assert o2.y == 0


def test_timeline_operator_add(tl, o1):
    tl.to(o1, 10, {'x': 100})
    tl2 = Timeline().to(o1, 10, {'y': 100})
    tl3 = tl + tl2

    ren = tl3.get_renderer()

    ren.render(5)
    assert o1.x == 50
    assert o1.y == 0

    ren.render(15)
    assert o1.x == 100
    assert o1.y == 50


def test_timeline_operator_iadd(tl, o1):
    tl.to(o1, 10, {'x': 100})
    tl += Timeline().to(o1, 10, {'y': 100})

    ren = tl.get_renderer()

    ren.render(5)
    assert o1.x == 50
    assert o1.y == 0

    ren.render(15)
    assert o1.x == 100
    assert o1.y == 50


def test_timeline_operator_and(tl, o1):
    tl.to(o1, 10, {'x': 100})
    tl2 = Timeline().to(o1, 10, {'y': 100})
    tl3 = tl & tl2

    ren = tl3.get_renderer()

    ren.render(5)
    assert o1.x == 50
    assert o1.y == 50


def test_timeline_operator_iand(tl, o1):
    tl.to(o1, 10, {'x': 100})
    tl &= Timeline().to(o1, 10, {'y': 100})

    ren = tl.get_renderer()

    ren.render(5)
    assert o1.x == 50
    assert o1.y == 50


def test_timeline_opertor_mul(tl, o1):
    tl2 = tl.to(o1, 10, {'x': 100}) * 2
    assert tl2.duration == 20

    ren = tl2.get_renderer()

    ren.render(5)
    assert o1.x == 50
    ren.render(10)
    assert o1.x == 0
    ren.render(15)
    assert o1.x == 50


def test_timeline_opertor_imul(tl, o1):
    tl = tl.to(o1, 10, {'x': 100})
    tl *= 2
    assert tl.duration == 20


def test_timeline_opertor_reverse(tl, o1):
    tl.to(o1, 10, {'x': 100}).to(o1, 10, {'y': 100})
    ~tl

    ren = tl.get_renderer()

    #ren.render(0)
    ##assert o1.x == 100
    #assert o1.y == 100
    ren.render(5)
    assert o1.y == 50
    #assert o1.x == 100
    ren.render(15)
    assert o1.y == 0
    assert o1.x == 50
    ren.render(20)
    assert o1.x == 0
    assert o1.y == 0
