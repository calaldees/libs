from ..misc import random_string, now
from .events import SessionCreated

import logging
log = logging.getLogger(__name__)


GENERATED_IDENTITY_OVERLAYS = {
    'timestamp': lambda session: now()
}


def session_identity(request, session_keys={'id', }):
    # The session id is abstracted from the framework. Keep a count/track id's as session values
    if 'id' not in request.session:
        request.session['id'] = random_string()
        request.registry.notify(SessionCreated(request))
    identity_dict = {
        **{
            key: request.session.get(key, None)
            for key in session_keys
        },
        **{
            key: GENERATED_IDENTITY_OVERLAYS[key](request.session)
            for key in session_keys & GENERATED_IDENTITY_OVERLAYS.keys()
        },
    }
    assert identity_dict.keys() >= session_keys
    return identity_dict
