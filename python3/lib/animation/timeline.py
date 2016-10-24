from collections import namedtuple
from functools import wraps

import logging
log = logging.getLogger(__name__)


class Timeline(object):
    """
    Inspired by 'GSAP (GreenSock Animation Platform)' http://greensock.com/
    A generalised animation framework for tweeing python attributes.
    """
    AnimationItem = namedtuple('AnimationItem', ('timestamp', 'element', 'duration', 'values'))

    def __init__(self, delay=0, repeat=0, repeatDelay=0, onUpdate=None, onRepeat=None, onComplete=None):
        self._animation_items = []
        self._lable_timestamps = {}

    # Build --------------------------------------------------------------------

    @invalidate_timeline_cache
    def to(self, elements, duration, values, label=None):
        if not hasattr(elements, '__iter__'):
            elements = (elements, )
        timestamp = 0  # TODO
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
        log.debug('TODO: cache cleared')
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
