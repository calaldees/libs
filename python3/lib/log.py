from .misc import now, json_string

import logging
event_log = logging.getLogger('json_log_event')


def log_event(request, **kwargs):
    """
    It is expected that python's logging framework is used to output these
    events to the correct destination
    """
    data = kwargs

    event = data.get('event')
    try:
        event = request.matched_route.name
    except:
        pass
        # TODO: name from traversal context?

    data.update({
        'event': event,
        'session_id': request.session.get('id'),
        'ip': request.environ.get('REMOTE_ADDR'),
        'timestamp': now(),
    })
    event_log.info(json_string(data))
