from decorator import decorator

import logging
log = logging.getLogger(__name__)

from ..misc import random_string
from . import request_from_args
from .auto_format import action_error


#-------------------------------------------------------------------------------
# Overlay Identity
#-------------------------------------------------------------------------------

def overlay_session_identity(session_keys=('id',)):
    """
    Decorator to post process an action_ok dict and append the current users details to the return
    This ensure that our local templates and external client's have the same data to work with when rendering
    
    session_keys are the keys from the session that will be surfaced as the identity dict
    """
    def _overlay_identity(target, *args, **kwargs):
        request = request_from_args(args)
        if 'internal_request' in request.matchdict:  # Abort if internal call
            return target(*args, **kwargs)
        
        # The session id is abstracted from the framework. Keep a count/track id's as session values
        if 'id' not in request.session:
            request.session['id'] = random_string()
        
        def overlay_identity_onto(target_dict):
            identity_dict = {}
            for key in session_keys:
                identity_dict[key] = request.session.get(key,None)
            target_dict['identity'] = identity_dict
    
        try:
            result = target(*args, **kwargs)
        except action_error as ae:
            # overlay identity onto action_errors
            overlay_identity_onto(ae.d)
            raise ae
        
        # Overlay a new dict called identity onto each request
        if isinstance(result, dict):
            overlay_identity_onto(result)
        
        return result

    return decorator(_overlay_identity)
