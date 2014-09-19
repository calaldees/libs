import hashlib
import time

from ..pyramid_helpers.auto_format import action_ok, action_error

import logging
log = logging.getLogger(__name__)

login_provider = None
user_store = None


def logout(request):
    request.session['user'] = {}
    return action_ok()


def login(request, login_provider, user_store):
    """

    """
    assert login_provider
    assert user_store
    user = None
    provider_token = None

    # Step 1 - Direct user to 3rd party login dialog ---------------------------
    if not request.session.get('user') and not request.params:
        if 'csrf_token' not in request.session:
            sha1_hash = hashlib.sha1()
            sha1_hash.update(str(time.time()).encode('utf-8'))
            request.session['csrf_token'] = sha1_hash.hexdigest()
        data = login_provider.login_dialog_data(request)
        if data:
            return action_ok(data=data)  # template will be rendered with this data
        # else this provider dose not require a dialog or redirect step - could be a mock for testing

    # Step 2 - Lookup full 3rd party access_token with token from dialog -------
    provider_token = login_provider.verify_cridentials(request)

    if not provider_token:
        error_message = 'error verifying cridentials'
        log.error(error_message)
        raise action_error(message=error_message)

    # Step 3 - Lookup local user_id OR create local user with details from 3rd party service
    user = user_store.get_user_from_token(provider_token)
    if not user:
        user_store.create_user(
            provider_token,
            login_provider.aquire_additional_user_details(provider_token),
        )
        user = user_store.get_user_from_token(provider_token)

    if not user:
        error_message = 'no user'.format()
        request.session['user'] = {}
        log.error(error_message)
        raise action_error(message=error_message)

    # Step 4 - set session details ---------------------------------------------
    request.session['user'] = user_store.user_to_session_dict(user)

    return action_ok()
