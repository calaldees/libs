import datetime


try:
    import dateutil.parser
    dateutil_parser = dateutil.parser.parser()
except ImportError:
    from unittest.mock import Mock
    dateutil_parser = Mock()



# TODO - @property to get/set now?
_now_override = None
def now(new_override=None):
    global _now_override
    if new_override:
        _now_override = new_override
    if _now_override:
        return _now_override
    return datetime.datetime.now()


def epoc(datetime_obj):
    return (datetime_obj - datetime.datetime.utcfromtimestamp(0)).total_seconds()


def normalize_datetime(d=None, accuracy='hour'):
    """
    Normalizez datetime down to hour or day
    Dates are immutable (thank god)
    """
    if not d:
        d = now()
    if not accuracy or accuracy == 'none':
        return None
    elif accuracy == 'hour':
        return d.replace(minute=0, second=0, microsecond=0)
    elif accuracy == 'day' :
        return d.replace(minute=0, second=0, microsecond=0, hour=0)
    elif accuracy == 'week':
        return d.replace(minute=0, second=0, microsecond=0, hour=0) - datetime.timedelta(days=d.weekday())
    return d


def parse_timedelta(text):
    """
    Takes string and converts to timedelta

    ##>>> parse_timedelta('00:01:00.01')
    ##datetime.timedelta(0, 60, 1)

    >>> parse_timedelta('00:00:01.00')
    datetime.timedelta(0, 1)
    >>> parse_timedelta('01:00:00')
    datetime.timedelta(0, 3600)
    >>> parse_timedelta('5')
    datetime.timedelta(0, 5)
    >>> parse_timedelta('1:01')
    datetime.timedelta(0, 3660)
    """
    hours = "0"
    minutes = "0"
    seconds = "0"
    milliseconds = "0"
    time_components = text.strip().split(':')
    if len(time_components) == 1:
        seconds = time_components[0]
    elif len(time_components) == 2:
        hours = time_components[0]
        minutes = time_components[1]
    elif len(time_components) == 3:
        hours = time_components[0]
        minutes = time_components[1]
        seconds = time_components[2]
    second_components = seconds.split('.')
    if len(second_components) == 2:
        seconds = second_components[0]
        milliseconds = second_components[1]
    hours = int(hours)
    minutes = int(minutes)
    seconds = int(seconds)
    milliseconds = int(milliseconds)
    assert hours >= 0
    assert minutes >= 0
    assert seconds >= 0
    assert milliseconds == 0, 'milliseconds are not implemented properly .01 is parsed as int(01), this is incorrect, fix this!' 
    return datetime.timedelta(
        seconds=seconds + minutes*60 + hours*60*60,
        milliseconds=milliseconds
    )
