import math
from collections import namedtuple


_timesignature = namedtuple('timesignature', ['beats_in_bar', 'one_beat'])


def parse_timesignature(value):
    """
    >>> parse_timesignature('4:4')
    timesignature(beats_in_bar=4, one_beat=4)
    >>> parse_timesignature('3:4')
    timesignature(beats_in_bar=3, one_beat=4)
    >>> parse_timesignature(parse_timesignature('4:8'))
    timesignature(beats_in_bar=4, one_beat=8)
    """
    if isinstance(value, str):
        return _timesignature(*map(int, value.split(':')))
    return value


def timecode_to_beatcount(timecode, timesignature=parse_timesignature('4:4')):
    """
    There are lamentably no standards in music timecodes.
    This Parse's timecode that matchs the Ableton time system.
    Further parser 'modes' could be passed to work like cuebase and other systems.

    >>> timecode_to_beatcount('1.1.1')
    0.0
    >>> timecode_to_beatcount('1.1.2')
    0.25
    >>> timecode_to_beatcount('1.1.3')
    0.5
    >>> timecode_to_beatcount('1.2.1')
    1.0
    >>> timecode_to_beatcount('1.3.1')
    2.0
    >>> timecode_to_beatcount('1.4.1')
    3.0
    >>> timecode_to_beatcount('2.1.1')
    4.0
    >>> timecode_to_beatcount('2.1.1', '3:4')
    3.0
    >>> timecode_to_beatcount('3.1.1', '3:4')
    6.0
    >>> timecode_to_beatcount('21.1.1', '3:4')
    60.0
    >>> timecode_to_beatcount('2.1.1', '8:4')
    8.0
    >>> timecode_to_beatcount('1.5.1', '8:4')
    4.0
    >>> timecode_to_beatcount('8.5.1', '8:4')
    60.0
    >>> timecode_to_beatcount('16.1.1', '4:4')
    60.0
    """
    timesignature = parse_timesignature(timesignature)
    if (isinstance(timecode, str)):
        timecode = tuple(map(int, timecode.split('.')))
    return sum(
        (timecode_component - 1) / pow(timesignature.beats_in_bar, index - 1)
        for index, timecode_component in enumerate(timecode)
    )


def beatcount_to_timecode(beat, timesignature=parse_timesignature('4:4'), slices=3):
    """
    >>> beatcount_to_timecode(5.25)
    '2.2.2'
    >>> beatcount_to_timecode(2.0)
    '1.3.1'
    >>> beatcount_to_timecode(0)
    '1.1.1'
    >>> beatcount_to_timecode(4.0)
    '2.1.1'
    >>> beatcount_to_timecode(60.0)
    '16.1.1'
    >>> beatcount_to_timecode(2.0)
    '1.3.1'
    >>> beatcount_to_timecode(0.25)
    '1.1.2'
    >>> beatcount_to_timecode(3, '3:4')
    '2.1.1'
    """
    timesignature = parse_timesignature(timesignature)
    def _pop_beat(accumulator, value):
        value_slice = int(value // timesignature.beats_in_bar)
        accumulator.append(str(1 + value_slice))
        if len(accumulator) < slices:
            _pop_beat(accumulator, (value - (value_slice * timesignature.beats_in_bar)) * timesignature.beats_in_bar)
        return accumulator
    return '.'.join(_pop_beat([], beat))


def seconds_to_beatcount(time_current, bpm, time_start=0.0):
    """
    Given a bpm and a time in seconds, what beat are we on
    """
    # TODO - needs reworking?
    return max(0.0, ((time_current - time_start) / 60) * bpm)


def timecode_to_seconds(timecode, bpm, timesignature=parse_timesignature('4:4')):
    """
    >>> timecode_to_seconds('1.1.1', 60, '4:4')
    0.0
    >>> timecode_to_seconds('1.2.1', 60, '4:4')
    1.0
    >>> timecode_to_seconds('1.3.1', 60, '4:4')
    2.0
    >>> timecode_to_seconds('2.1.1', 60, '4:4')
    4.0
    >>> timecode_to_seconds('16.1.1', 60, '4:4')
    60.0
    >>> timecode_to_seconds('2.1.1', 60, '4:8')
    2.0
    >>> timecode_to_seconds('31.1.1', 60, '4:8')
    60.0
    >>> timecode_to_seconds('2.1.1', 60, '8:4')
    8.0
    >>> timecode_to_seconds('8.5.1', 60, '8:4')
    60.0
    >>> timecode_to_seconds('2.1.1', 30, '4:8')
    4.0
    >>> timecode_to_seconds('2.1.1', 30, '8:4')
    16.0
    >>> timecode_to_seconds('2.1.1', 60, '3:4')
    3.0
    >>> timecode_to_seconds('21.1.1', 60, '3:4')
    60.0
    >>> timecode_to_seconds('5.1.1', 60, '3:4')
    12.0
    >>> round(timecode_to_seconds('14.3.3', 134, '3:4'), 3)
    18.657
    >>> round(timecode_to_seconds('11.2.3.1', 134), 3)
    18.582
    """
    timesignature = parse_timesignature(timesignature)
    return timecode_to_beatcount(timecode, timesignature) * (60 / bpm) * (4 / timesignature.one_beat)


def seconds_to_timecode(seconds, bpm, timesignature=parse_timesignature('4:4')):
    """
    >>> seconds_to_timecode(0.0, 60, '4:4')
    '1.1.1'
    >>> seconds_to_timecode(4.0, 60, '4:4')
    '2.1.1'
    >>> seconds_to_timecode(3.0, 60, '3:4')
    '2.1.1'
    >>> seconds_to_timecode(60.0, 60, '8:4')
    '8.5.1'
    >>> seconds_to_timecode(60.0, 60, '4:8')
    '31.1.1'
    """
    timesignature = parse_timesignature(timesignature)
    return beatcount_to_timecode(seconds / (60 / bpm) / (4 / timesignature.one_beat), timesignature)


def next_frame_from_timestamp(timestamp, frame_rate):
    return math.ceil(timestamp * frame_rate)


def nearest_timecode_to_next_frame(time_current, frame_rate):
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
    return next_frame_from_time_current(time_current, frame_rate) / frame_rate
