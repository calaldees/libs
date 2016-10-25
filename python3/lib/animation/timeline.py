from collections import namedtuple
from functools import wraps
from numbers import Number
from functools import reduce
from copy import copy

import logging
log = logging.getLogger(__name__)


class Timeline(object):
    """
    Inspired by
      * GSAP (GreenSock Animation Platform) - http://greensock.com/
      * Kivy - https://kivy.org/docs/api-kivy.animation.html
    A generalised animation framework for tweeing python attributes.
    """
    AnimationItem = namedtuple('AnimationItem', ('timestamp', 'element', 'duration', 'values'))

    def __init__(self, delay=0, repeat=0, repeatDelay=0, onUpdate=None, onRepeat=None, onComplete=None):
        self._animation_items = []
        self._label_timestamps = {}
        self.duration = 0

    # Properties ---------------------------------------------------------------

    @property
    def _duration(self):
        return reduce(
            lambda accumulator, item: max(accumulator, item.timestamp + item.duration),
            self._animation_items, 0
        )

    # Build --------------------------------------------------------------------

    @invalidate_timeline_cache
    def to(self, elements, duration, values, label=None):
        if not hasattr(elements, '__iter__'):
            elements = (elements, )

        # Lookup/Calculate label timestamp
        timestamp = self.duration
        if isinstance(label, Number):
            timestamp += label
        else:
            timestamp = self._label_timestamps.setdefault(label, timestamp)

        for element in elements:
            self._animation_items.append(AnimationItem(timestamp, element, duration, values))
        return self

    def set(self, elements, values, label=None):
        return self.to(elements, 0, values, label)

    def staggerTo(self, elements, duration, values, offset, label=None):
        item_duration = duration - (offset * len(elements))
        for element in elements:
            self.to(element, item_duration, values, label=-item_duration + offset)
        return self

    # Control ------------------------------------------------------------------

    def render(self, timecode):
        pass

    # Decorators ---------------------------------------------------------------

    def _invalidate_timeline_cache(self):
        self.duration = self._duration
    def invalidate_timeline_cache(original_function=None):
        """
        Decorator to place on methods that modify the timeline state
        this invalidates
        """
        def _decorate(function):
            @wraps(function)
            def wrapped_function(self, *args, **kwargs):
                _return = function(self, *args, **kwargs)
                self._invalidate_timeline_cache()
                return _return
            return wrapped_function
        return _decorate(original_function) if original_function else _decorate

    def elements_to_multiple_calls(original_function=None):
        """
        Convert element iterables into single calls
        """
        def _decorate(function):
            @wraps(function)
            def wrapped_function(self, elements, *args, **kwargs):
                if isinstance(elements, str) or not hasattr(str, '__iter__'):
                    return function(self, elements, *args, **kwargs)
                for element in elements:
                    _return = function(self, element, *args, **kwargs)
                return _return
            return wrapped_function
        return _decorate(original_function) if original_function else _decorate


    # Operators ----------------------------------------------------------------

    def __copy__(self):
        t = Timeline()
        for field in ('_animation_items', '_label_timestamps', '_head_timestamp'):
            setattr(t, field, copy(getattr(self, field)))
        return t

    def _add_(timeline1, timeline2):
        timeline1._animation_items += [
            self.AnimationItem(timestamp=timeline1.duration + i.timestamp, element=i.element, duration=i.duration, values=i.values)
            for i in timeline2._animation_items
        ]
        timeline1._label_timestamps.update({
            label: timeline1.duration + timestamp
            for label, timestamp in timeline2._label_timestamps.items()
        })
        timeline1._invalidate_timeline_cache()

    def __add__(timeline1, timeline2):
        t = copy(timeline1)
        t._and_(timeline2)
        return t

    def __iadd__(self, other):
        self._add_(other)

    def __concat__(self, other):
        pass

    def _and_(timeline1, timeline2):
        timeline1._animation_items += timeline2._animation_items
        timeline1._label_timestamps.update(timeline2._label_timestamps)
        timeline1._invalidate_timeline_cache()

    def __and__(timeline1, timeline2):
        t = copy(timeline1)
        t._and_(timeline2)
        return t

    def __iand__(self, other):
        self._and_(other)

    def _reverse_(timeline):
        timeline._animation_items = [
            self.AnimationItem(timestamp=timeline.duration - i.timestamp - i.duration, element=i.element, duration=i.duration, values=i.values)
            for i in reversed(timeline._animation_items)
        ]

    def __reversed__(self):
        self._reverse_()

    def __invert__(self):
        self._reverse_()

    def _mul_(timeline, repeats):
        assert isinstance(repeats, int)
        return [
            self.AnimationItem(timestamp=i.timestamp * r, element=i.element, duration=i.duration, values=i.values)
            for i in timeline._animation_items
            for r in repeats
        ]

    def __mul__(timeline, repeats):
        t = copy(timeline)
        t._animation_items = self._mul_(repeats)
        return t

    def __imul__(self, repeats):
        self._animation_items = self._mul_(self, repeats)
