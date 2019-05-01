from collections import namedtuple
from functools import reduce
from numbers import Number
from copy import copy

from ..data import blend, get_attr_or_item
from ..limit import limit

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
    class AnimationItem():
        def __init__(self, timestamp=None, duration=None, render_item_func=None, tween=None):
            assert timestamp != None  # TODO: could this be >= 0 like duration? or do we accept negative timestamps?
            assert duration >= 0, 'Duration must be positive value'
            assert callable(render_item_func)
            self.timestamp = timestamp
            self.duration = duration
            self.render_item_func = render_item_func
            self.tween = tween or Timeline.Tween.tween_linear

        def __repr__(self):
            return f'<AnimationItem timestamp={self.timestamp} duration={self.duration} tween={self.tween} render_item_func={vars(self.render_item_func)}>'

        @property
        def element(self):
            """
            For backwards compatability with triggerline
            May need to think about a different implementation?
            """
            # TODO: maybe add 'try' and return None if render_item_func does not support the default interface?
            return self.render_item_func._element

        @property
        def timestamp_end(self):
            return self.timestamp + self.duration

        def _asdict(self):
            return copy(vars(self))

        def copy_and_update(self, **kwargs):
            return Timeline.AnimationItem(**{**self._asdict(), **kwargs})


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

    def _resolve_timestamp(self, timestamp, offset=0):
        if isinstance(timestamp, str):
            timestamp = self._label_timestamps.setdefault(timestamp, self.duration)
        elif timestamp == None:  # If no timestamp provided, return end of current timeline, this is like appending to end
            timestamp = self.duration
        timestamp += offset
        return timestamp

    def add_label(self, name, timestamp):
        self._label_timestamps[name] = timestamp

    def animation_item(self, timestamp, duration, render_item_func, tween=None, offset=0):
        """
        render_item_func takes a value between 0 and 1 and sets the values on element
        """
        self._animation_items.append(
            self.AnimationItem(self._resolve_timestamp(timestamp, offset), duration, render_item_func, tween)
        )
        self._invalidate_timeline_cache()
        return self

    # FromTo Layer -------------------------------------------------------------

    @staticmethod
    def _get_default_render_item_func(element, valuesFrom={}, valuesTo={}):
        assert valuesFrom or valuesTo, 'No animation values provided'
        assert isinstance(valuesFrom, dict)
        assert isinstance(valuesTo, dict)
        if valuesFrom and valuesTo:
            assert valuesFrom.keys() == valuesTo.keys(), 'from/to keys should be symmetrical'
        valuesFrom = copy(valuesFrom)
        valuesTo = copy(valuesTo)

        def _derive_missing_from_to_values():
            if bool(valuesFrom) ^ bool(valuesTo):
                source = valuesFrom or valuesTo
                destination = valuesFrom if not valuesFrom else valuesTo
                for field in source.keys():
                    destination[field] = copy(get_attr_or_item(element, field))
            assert valuesFrom.keys() == valuesTo.keys(), 'from/to animations should be symmetrical'  # Temp assertion for development

        def _render_item(tween_pos):
            _derive_missing_from_to_values()  # done at the absolute final moment before the item is animated
            blend(valuesFrom, valuesTo, target=element, blend=min(max(tween_pos, 0), 1))

        _render_item._element = element  # for debugging the function
        _render_item._valuesFrom = valuesFrom
        _render_item._valuesTo = valuesTo

        return _render_item

    def from_to(self, elements, duration, valuesFrom={}, valuesTo={}, tween=None, timestamp=None, offset=0):
        assert elements, 'No elements to animate'
        if not hasattr(elements, '__iter__') or isinstance(elements, dict):  # TODO: why is isinstance(dict) here? remove?
            elements = (elements, )

        timestamp = self._resolve_timestamp(timestamp, offset)
        for element in elements:
            self.animation_item(timestamp, duration, self._get_default_render_item_func(element, valuesFrom, valuesTo), tween)
        return self

    def to(self, elements, duration, valuesTo, tween=None, timestamp=None):
        return self.from_to(elements, duration, valuesTo=valuesTo, tween=tween, timestamp=timestamp)

    def from_(self, elements, duration, values, tween=None, timestamp=None):
        return self.from_to(elements, duration, valuesFrom=values, tween=tween, timestamp=timestamp)

    def set_(self, elements, values, timestamp=None):
        return self.to(elements, 0, valuesTo=values, timestamp=timestamp)

    def staggerTo(self, elements, duration, valuesTo, item_delay, tween=None, timestamp=None):
        """
        duration is the duration of each individual element
        Total time = duration + (item_delay * num of elements)
        """
        # TODO: Incorporate tween into item_delay?
        timestamp = self._resolve_timestamp(timestamp)
        for index, element in enumerate(elements):
            self.to(element, duration, valuesTo=valuesTo, tween=tween, timestamp=timestamp + (index * item_delay))
        return self

    # Split --------------------------------------------------------------------

    def split(self, *timestamps):
        """
        Split a timeline at n timestamps and return n + 1 timelines
        """
        timestamps_a = (0,) + tuple(timestamps)
        timestamps_b = tuple(timestamps) + (self.duration,)
        for timestamp_start, timestamp_end in zip(timestamps_a, timestamps_b):
            def _in(timestamp):
                return timestamp >= timestamp_start and timestamp <= timestamp_end
            t = Timeline()
            for i in self._animation_items:
                if i.timestamp_end < timestamp_start or i.timestamp > timestamp_end:
                    continue
                original_duration = i.duration
                original_timestamp = i.timestamp
                original_timestamp_end = i.timestamp_end
                _i = i._asdict()
                if _in(i.timestamp) and _in(i.timestamp_end):
                    _i['timestamp'] += -timestamp_start
                if not _in(i.timestamp) and _in(i.timestamp_end):
                    new_duration = original_duration - (timestamp_start - original_timestamp)
                    _i['timestamp'] = 0
                    _i['duration'] = new_duration
                    _, _i['tween'] = Timeline.Tween.tween_progress_split(_i['tween'], (timestamp_start - original_timestamp) / original_duration)
                if _in(i.timestamp) and not _in(i.timestamp_end):
                    new_timestamp = _i['timestamp'] - timestamp_start
                    new_duration = timestamp_end - new_timestamp
                    _i['timestamp'] = new_timestamp
                    _i['duration'] = new_duration
                    _i['tween'], _ = Timeline.Tween.tween_progress_split(_i['tween'], new_duration / original_duration)
                if not _in(i.timestamp) and not _in(i.timestamp_end):
                    new_duration = timestamp_end - timestamp_start
                    new_timestamp_start = timestamp_start - original_timestamp
                    _i['timestamp'] = 0
                    _i['duration'] = new_duration
                    _, _i['tween'], _ = Timeline.Tween.tween_progress_split(
                        _i['tween'],
                        new_timestamp_start / original_duration,
                        (new_timestamp_start + new_duration) / original_duration,
                    )
                t._animation_items.append(Timeline.AnimationItem(**_i))
            t._label_timestamps = {label: timestamp - timestamp_start for label, timestamp in self._label_timestamps.items() if _in(timestamp)}
            yield t

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
            return i.copy_and_update(timestamp=i.timestamp + timeline1.duration)
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
        duration = timeline.duration
        timeline._animation_items = [
            i.copy_and_update(timestamp=i.timestamp + (duration * r))
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
        raise NotImplemented()

    def _reverse_(timeline):
        def reverse_item(i):
            return i.copy_and_update(
                timestamp=timeline.duration - i.timestamp - i.duration,
                tween=i.tween.tween_func if getattr(i.tween, 'inverted', False) else Timeline.Tween.tween_invert(i.tween)
            )
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

    def get_renderer(self, *args, **kwargs):
        """
        Return a new renderer to modify the animation items
        The returned rendering caches the animation progress state
        """
        return Timeline.Renderer(self, *args, **kwargs)

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

            # Update _active items list for current timecode
            has_more_items = lambda: self._next_item_index < len(self._items)
            timecode_is_in_next_item = lambda: timecode >= self._next_item.timestamp
            while has_more_items() and timecode_is_in_next_item():
                self._active.append(self._next_item)
                self._next_item_index += 1
            self._active.sort(key=lambda i: i.timestamp_end)  # Sort in order of expiry for efficient removal

            # Render _active items
            for i in self._active:
                if i.duration == 0 or i.timestamp_end < timecode:
                    normalized_pos = 1
                else:
                    normalized_pos = limit((timecode - i.timestamp) / i.duration)  # Little unsure of using `limit` here. We should never get values > 1. Could be a rounding error. Maybe this will hide future problems?
                i.render_item_func(i.tween(normalized_pos))

            # Expire passed animation items form _active
            while self._active and self._active[0].timestamp_end < timecode:
                self._active.pop(0)

            # Todo: Implement events
            #if timecode >= 1:
            #    if self.onComplete:
            #        self.onComplete()
            #else:
            #    if self.onUpdate:
            #        self.onUpdate()

        @property
        def _next_item(self):
            return self._items[self._next_item_index]


    # Tweens ---------------------------------------------------------------

    class Tween(object):
        """
        These tween functions support tween function modification.
        The tween functions themselves can be imported from https://github.com/asweigart/pytweening/blob/master/pytweening/__init__.py
        A handy visualisation of tween can be found at https://easings.net/en
        """

        @staticmethod
        def _checkRange(n):
            """Raises ValueError if the argument is not between 0.0 and 1.0."""
            if not 0.0 <= n <= 1.0:
                raise ValueError('Argument must be between 0.0 and 1.0.')

        @staticmethod
        def _split_values(*values, floor=0, ceiling=1):
            """
            >>> Timeline.Tween._split_values(0.5)
            ((0, 0.5), (0.5, 1))
            >>> Timeline.Tween._split_values(0.25, 0.75)
            ((0, 0.25), (0.25, 0.75), (0.75, 1))
            """
            values = tuple(values)
            assert all(True for value in values if floor < value < ceiling), f'all values must be between {floor} and {ceiling}'
            values_a = (floor,) + values
            values_b = values + (ceiling,)
            return tuple(zip(values_a, values_b))

        @staticmethod
        def _reframe_value(n, min=0, max=1):
            """
            >>> Timeline.Tween._reframe_value(0, min=0.5, max=1.0)
            0.5
            >>> Timeline.Tween._reframe_value(0.5, min=0.5, max=1.0)
            0.75
            """
            return min + ((max - min) * n)

        @staticmethod
        def _reframe_func(tween_func, min=0, max=1):
            """
            >>> reframed_func = Timeline.Tween._reframe_func(Timeline.Tween.tween_linear, min=0.5, max=1.0)
            >>> reframed_func(0)
            0.5
            >>> reframed_func(0.5)
            0.75
            """
            return lambda n: tween_func(Timeline.Tween._reframe_value(n, min, max))

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
        def tween_progress_split(tween_func, *split_values):
            """
            >>> tween_a, tween_b = Timeline.Tween.tween_progress_split(Timeline.Tween.tween_linear, 0.5)
            >>> tween_a(0)
            0.0
            >>> tween_a(0.5)
            0.25
            >>> tween_a(1)
            0.5
            >>> tween_b(0)
            0.5
            >>> tween_b(0.5)
            0.75
            >>> tween_b(1)
            1.0


            >>> tween_a, tween_b, tween_c = Timeline.Tween.tween_progress_split(Timeline.Tween.tween_linear, 0.2, 0.8)
            >>> tween_a(0.5)
            0.1
            >>> tween_b(0.5)
            0.5
            >>> tween_c(0.5)
            0.9
            """
            return (
                Timeline.Tween._reframe_func(tween_func, _low, _high)
                for _low, _high in Timeline.Tween._split_values(*split_values)
            )

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
