import math
from collections import namedtuple


# Time signiture ---------------------------------------------------------------

timesigniture = namedtuple('timesigniture', ['beats', 'bar'])


def parse_timesigniture(timesigniture_string):
    """
    >>> parse_timesigniture('4:4')
    timesigniture(beats=4, bar=4)
    """
    assert isinstance(timesigniture_string, str)
    return timesigniture(*map(int, timesigniture_string.split(':')))


def timecode_to_beat(timecode, timesigniture=parse_timesigniture('4:4')):
    """
    There are lementably no standards in music timecodes.
    This Parse's timecode that matchs the Ableton time system.
    Further parser 'modes' could be passed to work like cubase and other systems.

    >>> timecode_to_beat('4')
    4.0
    >>> timecode_to_beat('4.0.0')
    4.0
    >>> timecode_to_beat('4.1.0')
    4.25
    >>> timecode_to_beat('4.2.0')
    4.5
    >>> timecode_to_beat('4.2.2')
    4.625
    >>> timecode_to_beat('4.6.0', parse_timesigniture('4:8'))
    4.75
    """
    if (isinstance(timecode, str)):
        timecode = list(map(int, timecode.split('.')))
    return sum(timecode_component/pow(timesigniture.bar, index) for index, timecode_component in enumerate(timecode))


def beat_to_timecode(beat, timesigniture=parse_timesigniture('4:4')):
    """
    >>> beat_to_timecode(4.0)
    '4.0.0'
    >>> beat_to_timecode(4.25)
    '4.1.0'
    >>> beat_to_timecode(4.5)
    '4.2.0'
    >>> beat_to_timecode(4.625)
    '4.2.2'
    >>> beat_to_timecode(4.75, parse_timesigniture('4:8'))
    '4.6.0'
    """
    beat_number = int(beat//1)
    beat_remainder = beat % 1  # There must be a way to do this without the first number being a special case
    return '.'.join(map(str, map(int, [beat_number]+[(beat_remainder % (1/pow(timesigniture.bar, i)) // (1/pow(timesigniture.bar, i+1))) for i in range(0, 2)])))


def get_beat(time_current, bpm, time_start=0.0):
    """
    Given a bpm and a time in seconds, what beat are we on
    """
    return max(0.0, ((time_current - time_start) / 60) * bpm)


def get_time(timecode, timesigniture, bpm):
    """
    >>> get_time('1.0.0', parse_timesigniture('4:4'), 10)
    6.0
    >>> get_time('10.0.0', parse_timesigniture('4:4'), 10)
    60.0
    >>> get_time('11.0.0', parse_timesigniture('4:4'), 10)
    66.0
    >>> get_time('15.0.0', parse_timesigniture('4:4'), 60)
    15.0
    """
    return (timecode_to_beat(timecode, timesigniture) / bpm) * 60


def next_frame_from_timecode(timecode, frame_rate):
    return math.ceil(timecode * frame_rate)


def nearest_timecode_to_next_frame(timecode, frame_rate):
    """
    Match timecode to nearest 'next' frame

    >>> nearest_timecode_to_next_frame(11.0, 1)
    11.0
    >>> nearest_timecode_to_next_frame(11.1, 1)
    12.0
    >>> nearest_timecode_to_next_frame(11.0, 4)
    11.0
    >>> nearest_timecode_to_next_frame(11.72, 4)
    11.75
    >>> nearest_timecode_to_next_frame(11.1, 4)
    11.25
    """
    return next_frame_from_timecode(timecode, frame_rate) / frame_rate
