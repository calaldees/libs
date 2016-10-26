from collections import namedtuple
from functools import wraps, reduce
from numbers import Number
from copy import copy

import logging
log = logging.getLogger(__name__)


class Timeline(object):
    """
    A generalised animation framework for tweeing python attributes.
    Inspired by:
      * GSAP (GreenSock Animation Platform) - http://greensock.com/
      * Kivy - https://kivy.org/docs/api-kivy.animation.html
    """
    AnimationItem = namedtuple('TimelineAnimationItem', ('timestamp', 'element', 'duration', 'valuesFrom', 'valuesTo', 'timestamp_end'))
    Renderer = namedtuple('TimelineRenderer', ('items', 'active'))

    def __init__(self, delay=0, repeat=0, repeatDelay=0, onUpdate=None, onRepeat=None, onComplete=None):
        self._animation_items = []
        self._label_timestamps = {}
        self._invalidate_timeline_cache()

    # Properties ---------------------------------------------------------------

    @property
    def _duration(self):
        return reduce(
            lambda accumulator, i: max(accumulator, i.timestamp_end),
            self._animation_items, 0
        )

    # Build --------------------------------------------------------------------

    def add_label(self, name, timestamp):
        self._label_timestamps[name] = timestamp

    @invalidate_timeline_cache
    def from_to(self, elements, duration, valuesFrom={}, valuesTo={}, label=None):
        assert elements, 'No elements to animate'
        assert duration >= 0, 'Duration must be positive value'
        assert valuesFrom or valuesTo, 'No animation values provided'
        if valuesFrom and valuesTo:
            assert valuesFrom.keys() == valuesTo.keys(), 'from/to keys should be symetrical'
        if not hasattr(elements, '__iter__'):
            elements = (elements, )

        # Lookup/Calculate label timestamp
        timestamp = self.duration
        if isinstance(label, Number):
            timestamp += label
        else:
            timestamp = self._label_timestamps.setdefault(label, timestamp)

        for element in elements:
            self._animation_items.append(
                AnimationItem(timestamp, element, duration, valuesFrom=copy(valuesFrom), valuesTo=copy(valuesTo), timestamp_end=timestamp + duration)
            )
        return self

    def to(self, elements, duration, values, label=None):
        return self.from_to(elements, duration, valuesTo=values, label=label)

    def from(self, elements, duration, values, label=None):
        return self.from_to(elements, duration, valuesFrom=values, label=label)

    def set(self, elements, values, label=None):
        return self.to(elements, 0, values, label)

    def staggerTo(self, elements, duration, values, offset, label=None):
        item_duration = duration - (offset * len(elements))
        for element in elements:
            self.to(element, item_duration, valuesTo=values, label=-item_duration + offset)
        return self

    # Control ------------------------------------------------------------------

    @property
    def renderer(self):
        """
        Return a new renderer to modify the animation items
        The returned rendering caches the animation progress state
        """
        return Timeline.Renderer(self)

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
        assert isinstance(timeline1, Timeline)
        assert isinstance(timeline2, Timeline)
        def clone_item(i):
            vars = i._asdict()
            vars['timestamp'] += timeline1.duration
            return self.AnimationItem(**vars)
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
        t._and_(timeline2)
        return t

    def __iadd__(self, other):
        self._add_(other)

    def __concat__(self, other):
        pass

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

    def _reverse_(timeline):
        def clone_item(i):
            vars = i._asdict()
            vars['timestamp'] = timeline.duration - vars['timestamp'] - vars['duration']
            return self.AnimationItem(**vars)
        timeline._animation_items = [
            clone_item(i)
            for i in reversed(timeline._animation_items)
        ]

    def __reversed__(self):
        self._reverse_()

    def __invert__(self):
        self._reverse_()

    def _mul_(timeline, repeats):
        assert isinstance(timeline, Timeline)
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


    # Renderer -----------------------------------------------------------------

    class Renderer(object):
        def __init__(self, parent_timeline):
            self._items = tuple(sorted(self._animation_items, key=lambda item: item.timestamp))
            self.reset()

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
            while self._next_item_index < len(self._items) and self._next_item.timestamp > timecode:
                self._add_active_item(self._next_item)
                self._next_item_index += 1
            self._expire_passed_animation_items(timecode)

            # Render (as we have the current active items)
            for i in self._active:
                normalized_pos = (timecode - i.timestamp) / i.duration
                assert normalized_pos >= 0 and normalized_pos <= 1, 'Animation item should be in range'  # Temp assertion for development
                for field in i.valuesTo.keys():
                    #setattr(i.element, field, i.tween(i.valueTo))
                    pass

        @property
        def _next_item(self):
            return self._items[self._next_item_index]

        def _add_active_item(self, item):
            # Derive missing to/from values
            # This is done at the absolute final moment before the item is animated
            if item.valuesFrom ^ item.valuesTo:
                source = item.valuesFrom or item.valuesTo
                destination = item.valuesFrom if not item.valuesFrom else item.valuesTo
                for field in source.keys():
                    destination[field] = copy(getattr(item.element, field))
            assert item.valuesFrom.keys() == item.valuesTo.keys(), 'from/to animations should be symetrical'  # Temp assertion for development
            # Activate item
            self._items.append(item)
            # Sort in order of expiry for efficent removal
            self._items.sort(key=lambda i: i.timestamp_end)

        def _expire_passed_animation_items(self, timecode):
            while self._active and self._active[0].timestamp_end < timecode:
                self._active.pop(0)
