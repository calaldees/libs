import hashlib
import time

from ..misc import first
from ..pyramid_helpers.auto_format import action_ok, action_error

import logging
log = logging.getLogger(__name__)


class SocialLogin(object):

    def __init__(self, login_providers=None, user_store=None):
        self.login_providers = login_providers or {}
        self.user_store = user_store

    def add_login_provider(self, login_provider):
        self.login_providers[login_provider.name] = login_provider

    @property
    def html_includes(self):
        return ((login_provider.html_include for login_provider in self.login_providers.values() if login_provider.html_include))

    def logout(self, request):
        request.session['user'] = {}
        return action_ok()

    def login(self, request, login_providers=None, user_store=None):
        """

        """
        login_providers = login_providers or self.login_providers
        user_store = user_store or self.user_store
        assert login_providers
        assert user_store

        # Ensure login_provider is a dict - if single item, insert into dict
        if not isinstance(login_providers, dict):
            login_providers = {login_providers.name: login_providers}

        # Step 1 - Direct user to 3rd party login dialog ---------------------------
        if not request.session.get('user') and not request.params:
            # Create CSRF token
            if 'csrf_token' not in request.session:
                sha1_hash = hashlib.sha1()
                sha1_hash.update(str(time.time()).encode('utf-8'))
                request.session['csrf_token'] = sha1_hash.hexdigest()
            # Aquire lgoing data for each provider
            data = {}
            for login_provider in login_providers.values():
                data[login_provider.name] = login_provider.login_dialog_data(request)
            if any(data.values()):
                return action_ok(data=data)  # template will be rendered with the data from these providers
            # else this provider dose not require a dialog or redirect step - could be a mock for testing

        # Step 2 - Lookup full 3rd party access_token with token from dialog -------
        #  todo: this feels messy - better way to break on first provider token?
        provider_token = first((login_provider.verify_cridentials(request) for login_provider in login_providers.values()))

        if not provider_token:
            error_message = 'error verifying cridentials'
            log.error(error_message)
            raise action_error(message=error_message)

        # Step 3 - Lookup local user_id OR create local user with details from 3rd party service
        user = user_store.get_user_from_token(provider_token)
        if not user:
            user_store.create_user(
                provider_token,
                login_providers[provider_token.provider].aquire_additional_user_details(provider_token),
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
