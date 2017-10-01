import os.path
import json
import hashlib
import requests

from collections import namedtuple

ProviderToken = namedtuple('ProviderToken', ['provider', 'token', 'response'])

from . import facebook

import logging
log = logging.getLogger(__name__)


class ILoginProvider(object):
    """
    Not needed, but here to document the methods a LoginProvider should implement
    """
    name = 'unknown'

    def __init__(self):
        pass

    @property
    def html_include(self):
        return ''

    def login_dialog_data(self, request):
        """
        Should check if the required state is present to show dialog
        Then return dict with details for this provider for the template to render

        run_js
        redirect_url

        """
        return {}

    def verify_cridentials(self, request):
        """
        Returns a ProviderToken
        """
        return None

    def aquire_additional_user_details(self, provider_token):
        """
        """
        return {}


class IUserStore(object):
    """
    """
    def __init__(self):
        pass

    def get_user_from_token(self, provider_token):
        """
        a provider_token has
          .provider (the string of the provider)
          .token (the token given)
        This is to lookup a user from a local db store
        should return None if no user is found
        """
        pass

    def create_user(self, provider_token, data):
        """
        No need to return anything
        This function creates a user in perisistant store.
        The user is always retrived by .get_user_from_token
        """
        pass

    def user_to_session_dict(self, user):
        """
        Convert a user object into a dict for the session
        We may not want all of the data in the object in the session
        """
        pass


class NullLoginProvider(ILoginProvider):

    @property
    def html_include(self):
        return """<!-- NullLoginProvider javascript -->"""

    def verify_cridentials(self, request):
        return ProviderToken('', '', '')


class LoginProviderException(Exception):
    failed_to_verify_cridentials = 1


class FacebookLogin(ILoginProvider):
    name = 'facebook'

    def __init__(self, appid, secret, permissions):
        self.appid = appid
        self.secret = secret
        self.permissions = permissions

    def login_dialog_data(self, request):
        facebook_dialog_url = facebook.login_dialog_url(
            appid=self.appid,
            csrf_token=request.session['csrf_token'],
            permissions=self.permissions,
            redirect_uri=request.path_url,
        )
        return dict(redirect_url=facebook_dialog_url)

    def verify_cridentials(self, request):
        if request.params.get('code') and request.params.get('state'):
            if request.params.get('state') != request.session.get('csrf_token'):
                raise LoginProviderException('csrf mismatch')  # 400
            # Check submited code with facebook
            log.debug(' - '.join((str(self), 'verify_cridentials', 'request (short_lived_access_token)', request.params.get('code'))))
            response = facebook.call_api(
                'oauth/access_token',
                client_id=self.appid,
                client_secret=self.secret,
                redirect_uri=request.path_url,
                code=request.params.get('code'),
            )
            log.debug(' - '.join((str(self), 'verify_cridentials', 'response', str(response))))
            if response.get('error'):
                raise LoginProviderException(response.get('error'))

            # https://developers.facebook.com/docs/facebook-login/access-tokens#extending
            # http://stackoverflow.com/questions/17197970/facebook-permanent-page-access-token
            #log.debug(' - '.join((str(self), 'verify_cridentials', 'request (long_lived_access_token)', response.get('access_token'))))
            #response = facebook.call_api(
            #    'oauth/access_token',
            #    client_id=self.appid,
            #    client_secret=self.secret,
            #    grant_type='fb_exchange_token',
            #    fb_exchange_token=response.get('access_token'),
            #)

            # A massive hack - facebook access tokens are so shorted lived.
            # Facebook provides differnt access_tokens each login, so it's impossible to identify a returning users from this token.
            # Solution: Preload the 'response' with a basic user profile
            response.update(facebook.Facebook(access_token=response.get('access_token')).api('me'))

            return ProviderToken(self.name, response.get('id'), response)

    def aquire_additional_user_details(self, provider_token):
        # Hack - additiona details already present in provider_token.response
        # fb = facebook.Facebook(access_token=provider_token.token)
        # user_data = fb.api('me')
        user_data = provider_token.response
        user_data['avatar_url'] = facebook.endpoints['avatar'].format(provider_token.response.get('id'))
        return user_data


class PersonaLogin(ILoginProvider):
    """
    Depricated
    For reference only
    https://developer.mozilla.org/en-US/Persona/Quick_Setup
    """
    name = 'persona'

    def __init__(self, site_url=None, site_url_settings_key=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.site_url = site_url
        self.site_url_settings_key = site_url_settings_key or 'server.url'

    @property
    def html_include(self):
        """
        Rather than having to edit multiple static js files and headers
        Keep all js and server flow in one place
        Slightly fugly having js/html in a py file, but there are benefits

        needs to be set previously in the js for this to function
        var mozilla_persona = {
            currentUserEmail: null || 'email_of_logged_in_user@site.com',
            login_url: "/login",
            logout_url: "/logout"
        }

        'server.url' should be set in the pyramid registry

        -- Excert removed from header of template --
        <!-- Mozilla Persona -->
        <script type="text/javascript">
            var mozilla_persona = {
                currentUserEmail: null,
                login_url: "${login_url}",
                logout_url: "${logout_url}"
            };
            % if identity.get('user'):
            mozilla_persona.currentUserEmail = "${identity.get('user', {}).get('email', '')}";
            % endif
        </script>

        """
        return """
            <script src="https://login.persona.org/include.js"></script>
            <script type="text/javascript">
                (function() {
                    if (
                        typeof(navigator) != "object" ||
                        typeof(navigator.id) != "object"
                    ) {console.warn("Mozilla Persona not included. Login disabled"); return;}
                    if (
                        typeof(mozilla_persona) != "object"
                    ) {console.warn("Mozilla Persona settings not avalable. Login disabled"); return;}

                    navigator.id.watch({
                        loggedInUser: typeof(mozilla_persona) == "object" ? mozilla_persona.currentUserEmail : null,
                        onlogin: function(assertion) {
                            $.ajax({
                                type: 'POST',
                                url: mozilla_persona.login_url,
                                data: {assertion: assertion},
                                success: function(res, status, xhr) { window.location.reload(); },
                                error: function(xhr, status, err) {
                                    navigator.id.logout();
                                    alert("Login failure: " + err);
                                }
                            });
                        },
                        onlogout: function() {
                            $.ajax({
                                type: 'POST',
                                url: mozilla_persona.logout_url,
                                success: function(res, status, xhr) { window.location = "/"; },
                                error: function(xhr, status, err) { alert("Logout failure: " + err); }
                            });
                        }
                    });
                })();
            </script>
        """

    def login_dialog_data(self, request):
        if not request.params.get('assertion'):
            return dict(run_js='navigator.id.request();')

    def verify_cridentials(self, request):
        if request.params.get('assertion'):
            #"assertion=<ASSERTION>&audience=https://example.com:443" "https://verifier.login.persona.org/verify"
            response = requests.post(
                'https://verifier.login.persona.org/verify',
                data={
                    'assertion': request.params.get('assertion'),
                    'audience': self.site_url or request.registry.settings.get(self.site_url_settings_key),
                },
                verify=True
            )
            if response.ok:
                data = response.json()
                if data['status'] == 'okay':
                    return ProviderToken(self.name, data['email'], data)
            raise LoginProviderException(response.content)
        #raise LoginProviderException('no assertion provided')

    def aquire_additional_user_details(self, provider_token):
        data = dict(
            avatar_url='http://www.gravatar.com/avatar/{0}'.format(
                hashlib.md5(provider_token.token.encode('utf-8')).hexdigest()
            )
        )
        data.update(provider_token.response)
        data['name'] = data['email']
        return data


class GoogleLogin(ILoginProvider):
    """
    https://developers.google.com/identity/sign-in/web/server-side-flow
    https://console.developers.google.com/apis/credentials
    """
    name = 'google'

    def __init__(self, client_secret_file):
        super().__init__()
        assert os.path.isfile(client_secret_file)
        with open(client_secret_file, 'rt') as client_secret_filehandle:
            self.client_secret_file_data = json.load(client_secret_filehandle)
        self.client_secret_file = client_secret_file
        assert self.client_secret_file_data, f'google client_secret_file {client_secret_file} should parse json'

    @property
    def html_include(self):
        # <script src="//ajax.googleapis.com/ajax/libs/jquery/1.8.2/jquery.min.js"></script>
        return '''
            <script src="https://apis.google.com/js/client:platform.js?onload=start" async defer></script>
            <script>
                function start() {
                    gapi.load('auth2', function() {
                        auth2 = gapi.auth2.init({
                            client_id: '__CLIENT_ID__',
                            // Scopes to request in addition to 'profile' and 'email'
                            //scope: 'additional_scope'
                        });
                    });
                }
                function signInCallback(authResult) {
                    if (authResult['code']) {
                        $.post(window.location, authResult);
                    } else {
                        console.error('Google Auth', authResult);
                    }
                }
            </script>
        '''.replace('__CLIENT_ID__', self.client_secret_file_data['web']['client_id'])

    def login_dialog_data(self, request):
        return dict(run_js="auth2.grantOfflineAccess().then(signInCallback);")

    def verify_cridentials(self, request):
        if not request.params.get('code'):
            return
        from apiclient import discovery
        import httplib2
        from oauth2client import client

        if not request.headers.get('X-Requested-With'):
            raise 403  # TODO: raise real error

        import pdb ; pdb.set_trace()
        credentials = client.credentials_from_clientsecrets_and_code(
            self.client_secret_file,
            ['https://www.googleapis.com/auth/drive.appdata', 'profile', 'email'],
            request.params.get('code'),
        )

        # Call Google API
        http_auth = credentials.authorize(httplib2.Http())
        drive_service = discovery.build('drive', 'v3', http=http_auth)
        appfolder = drive_service.files().get(fileId='appfolder').execute()

        import pdb ; pdb.set_trace()

        return ProviderToken(self.name, credentials.id_token['email'], credentials.id_token)
        #raise LoginProviderException(response.content)

    def aquire_additional_user_details(self, provider_token):
        return {}
