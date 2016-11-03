from collections import namedtuple
from functools import wraps, reduce
from numbers import Number
from copy import copy

import logging
log = logging.getLogger(__name__)


class Timeline(object):
    """
    A generalized animation framework for tweening python attributes.
    Inspired by:
      * GSAP (GreenSock Animation Platform) - http://greensock.com/
      * Kivy - https://kivy.org/docs/api-kivy.animation.html
    Recommended that this is used with `pytweening`'s tween functions
    """
    AnimationItem = namedtuple('TimelineAnimationItem', ('timestamp', 'element', 'duration', 'valuesFrom', 'valuesTo', 'tween', 'timestamp_end'))

    def __init__(self):
        self._animation_items = []
        self._label_timestamps = {}
        self._duration = None

    # Properties ---------------------------------------------------------------

    @property
    def duration(self):
        if self._duration == None:
            self._duration = reduce(
                lambda accumulator, i: max(accumulator, i.timestamp_end),
                self._animation_items, 0
            ) or 0
        return self._duration

    def _invalidate_timeline_cache(self):
        self._duration = None

    # Build --------------------------------------------------------------------

    def add_label(self, name, timestamp):
        self._label_timestamps[name] = timestamp

    def from_to(self, elements, duration, valuesFrom={}, valuesTo={}, tween=None, label=None):
        assert elements, 'No elements to animate'
        assert duration >= 0, 'Duration must be positive value'
        assert valuesFrom or valuesTo, 'No animation values provided'
        if valuesFrom and valuesTo:
            assert valuesFrom.keys() == valuesTo.keys(), 'from/to keys should be symmetrical'

        tween = tween or Timeline.Tween.tween_linear
        if not hasattr(elements, '__iter__'):
            elements = (elements, )

        # Lookup/Calculate label timestamp
        timestamp = self.duration
        if isinstance(label, Number):
            timestamp += label
        elif label:
            timestamp = self._label_timestamps.setdefault(label, timestamp)

        for element in elements:
            self._animation_items.append(
                self.AnimationItem(
                    timestamp, element, duration,
                    tween=tween,
                    valuesFrom=copy(valuesFrom),
                    valuesTo=copy(valuesTo),
                    timestamp_end=timestamp + duration,
                )
            )

        self._invalidate_timeline_cache()
        return self

    def to(self, elements, duration, values, tween=None, label=None):
        return self.from_to(elements, duration, valuesTo=values, tween=tween, label=label)

    def from_(self, elements, duration, values, tween=None, label=None):
        return self.from_to(elements, duration, valuesFrom=values, tween=tween, label=label)

    def set_(self, elements, values, label=None):
        return self.to(elements, 0, values, label)

    def staggerTo(self, elements, duration, values, offset, tween=None, label=None):
        item_duration = duration - (offset * len(elements))
        for element in elements:
            self.to(element, item_duration, valuesTo=values, label=-item_duration + offset)
        return self

    # Control ------------------------------------------------------------------

    def get_renderer(self, *args, **kwargs):
        """
        Return a new renderer to modify the animation items
        The returned rendering caches the animation progress state
        """
        return Timeline.Renderer(self, *args, **kwargs)

    # Operators ----------------------------------------------------------------

    def __copy__(self):
        t = Timeline()
        for field in ('_animation_items', '_label_timestamps'):
            setattr(t, field, copy(getattr(self, field)))
        return t

    def _add_(timeline1, timeline2):
        assert isinstance(timeline1, Timeline)
        assert isinstance(timeline2, Timeline)
        def clone_item(i):
            vars = i._asdict()
            vars['timestamp'] += timeline1.duration
            vars['timestamp_end'] += timeline1.duration
            return Timeline.AnimationItem(**vars)
        timeline1._animation_items += [
            clone_item(i)
            for i in timeline2._animation_items
        ]
        timeline1._label_timestamps.update({
            label: timeline1.duration + timestamp
            for label, timestamp in timeline2._label_timestamps.items()
        })
        timeline1._invalidate_timeline_cache()

    def __add__(timeline1, timeline2):
        t = copy(timeline1)
        t._add_(timeline2)
        return t

    def __iadd__(self, other):
        self._add_(other)
        return self

    def __concat__(self, other):
        return self.__add__(other)

    def _and_(timeline1, timeline2):
        assert isinstance(timeline1, Timeline)
        assert isinstance(timeline2, Timeline)
        timeline1._animation_items += timeline2._animation_items
        timeline1._label_timestamps.update(timeline2._label_timestamps)
        timeline1._invalidate_timeline_cache()

    def __and__(timeline1, timeline2):
        t = copy(timeline1)
        t._and_(timeline2)
        return t

    def __iand__(self, other):
        self._and_(other)
        return self

    def _mul_(timeline, repeats):
        assert isinstance(timeline, Timeline)
        assert isinstance(repeats, int)
        timeline._animation_items = [
            timeline.AnimationItem(timestamp=i.timestamp + (timeline.duration * r), element=i.element, duration=i.duration, valuesTo=i.valuesTo, valuesFrom=i.valuesFrom, tween=i.tween, timestamp_end = i.timestamp_end + (timeline.duration * r))
            for r in range(repeats)
            for i in timeline._animation_items
        ]
        timeline._invalidate_timeline_cache()

    def __mul__(timeline, repeats):
        t = copy(timeline)
        t._mul_(repeats)
        return t

    def __imul__(self, repeats):
        self._mul_(repeats)
        return self

    def __truediv__(self, divisor):
        return self.__mul__(1/divisor)

    def _reverse_(timeline):
        def reverse_item(i):
            #Timeline.Renderer._derive_missing_from_to_values(i)
            vars = i._asdict()
            # Update position
            vars['timestamp'] = timeline.duration - vars['timestamp'] - vars['duration']
            vars['timestamp_end'] = vars['timestamp'] + vars['duration']
            # Swap from and to - (may not be needed as the tween is reversed)
            #temp = vars['valuesTo']
            #vars['valuesTo'] = vars['valuesFrom']
            #vars['valuesFrom'] = temp
            # Invert tween
            vars['tween'] = vars['tween'].tween_func if getattr(i.tween, 'inverted', False) else Timeline.Tween.tween_invert(vars['tween'])
            return Timeline.AnimationItem(**vars)
        timeline._animation_items = [
            reverse_item(i)
            for i in reversed(timeline._animation_items)
        ]

    def __reversed__(self):
        self._reverse_()

    def __invert__(self):
        t = copy(self)
        t._reverse_()
        return t

    def __neg__(self):
        return self.__invert__()

    # Renderer -----------------------------------------------------------------

    class Renderer(object):
        def __init__(self, parent_timeline, delay=0, repeat=0, repeatDelay=0, onUpdate=None, onRepeat=None, onComplete=None):
            self._items = tuple(sorted(parent_timeline._animation_items, key=lambda item: item.timestamp))
            self.reset()
            self.onUpdate = onUpdate
            self.onRepeat = onRepeat
            self.onComplete = onComplete

        def reset(self):
            self._active = []
            self._next_item_index = 0
            self._last_timecode = 0

        def render(self, timecode):
            # Active item cache only allows us to go forwards.
            # If we travel backwards in time reset the cache state and calculate form scratch
            if timecode < self._last_timecode:
                self.reset()
            self._last_timecode = timecode

            # Update active items list for current timecode
            has_more_items = lambda: self._next_item_index < len(self._items)
            timecode_is_in_next_item = lambda: timecode >= self._next_item.timestamp
            while has_more_items() and timecode_is_in_next_item():
                self._add_active_item(self._next_item)
                self._next_item_index += 1
            self._expire_passed_animation_items(timecode)

            # Render (as we have the current active items)
            for i in self._active:
                normalized_pos = (timecode - i.timestamp) / i.duration
                self._render_item(i, normalized_pos)

            if timecode >= 1:
                if self.onComplete:
                    self.onComplete()
            else:
                if self.onUpdate:
                    self.onUpdate()

        def _render_item(self, i, pos=1):
            for field in i.valuesTo.keys():
                setattr(
                    i.element,
                    field,
                    i.valuesFrom[field] + (i.tween(pos) * (i.valuesTo[field] - i.valuesFrom[field]))
                )

        @property
        def _next_item(self):
            return self._items[self._next_item_index]

        def _add_active_item(self, item):
            # This is done at the absolute final moment before the item is animated
            self._derive_missing_from_to_values(item)
            # Activate item
            self._active.append(item)
            # Sort in order of expiry for efficent removal
            self._active.sort(key=lambda i: i.timestamp_end)

        def _expire_passed_animation_items(self, timecode):
            while self._active and self._active[0].timestamp_end < timecode:
                self._render_item(self._active.pop(0))

        @staticmethod
        def _derive_missing_from_to_values(item):
            if bool(item.valuesFrom) ^ bool(item.valuesTo):
                source = item.valuesFrom or item.valuesTo
                destination = item.valuesFrom if not item.valuesFrom else item.valuesTo
                for field in source.keys():
                    destination[field] = copy(getattr(item.element, field))
            assert item.valuesFrom.keys() == item.valuesTo.keys(), 'from/to animations should be symmetrical'  # Temp assertion for development


    # Tweens ---------------------------------------------------------------

    class Tween(object):
        @staticmethod
        def _checkRange(n):
            """Raises ValueError if the argument is not between 0.0 and 1.0."""
            if not 0.0 <= n <= 1.0:
                raise ValueError('Argument must be between 0.0 and 1.0.')

        @staticmethod
        def tween_linear(n):
            """A linear tween function"""
            Timeline.Tween._checkRange(n)
            return n

        @staticmethod
        def tween_invert(tween_func):
            """
            """
            def _tween_invert(n):
                return tween_func(1 - n)
            _tween_invert.inverted = True
            _tween_invert.tween_func = tween_func
            return _tween_invert

        @staticmethod
        def tween_step(num_steps):
            """
            >>> tween_step = Timeline.Tween.tween_step
            >>> tween_step(4)(0)
            0.0
            >>> tween_step(4)(0.1)
            0.0
            >>> tween_step(4)(0.25)
            0.25
            >>> tween_step(4)(0.513)
            0.5
            >>> tween_step(4)(1)
            1.0
            """
            increment = 1 / num_steps
            def _tween_step(n):
                Timeline.Tween._checkRange(n)
                return (n // increment) * increment
            return _tween_step