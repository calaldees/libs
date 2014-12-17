from .misc import now


def log_event(request, **kwargs):
    data = kwargs
    data.update({
        'event': data.get('event') or request.matched_route.name,
        'user_id': request.session.get('id'),
        'user_ip': request.environ.get('REMOTE_ADDR'),
        'timestamp': int(now().timestamp()),
    })
    print(data)
