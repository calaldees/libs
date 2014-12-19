from .misc import now, json_string

import logging
event_log = logging.getLogger('json_log_event')


def log_event(request, **kwargs):
    """
    It is expected that python's logging framework is used to output these
    events to the correct destination
    """
    data = kwargs
    data.update({
        'event': data.get('event') or request.matched_route.name,
        'user_id': request.session.get('id'),
        'user_ip': request.environ.get('REMOTE_ADDR'),
        'timestamp': int(now().timestamp()),
    })
    event_log.info(json_string(data))
