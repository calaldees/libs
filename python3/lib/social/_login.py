import hashlib
import requests

from collections import namedtuple

ProviderToken = namedtuple('ProviderToken', ['provider', 'token'])

from . import facebook


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
        return ProviderToken('', '')


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
            response = facebook.call_api(
                'oauth/access_token',
                client_id     = self.appid,
                client_secret = self.secret,
                redirect_uri  = request.path_url,
                code          = request.params.get('code'),
            )
            if response.get('error'):
                raise LoginProviderException(response.get('error'))
            return ProviderToken(self.name, response.get('access_token'))

    def aquire_additional_user_details(provider_token):
        fb = facebook.facebook(access_token=provider_token.token)
        user_data = fb.api('me')
        user_data['avatar_img'] = facebook.endpoints['avatar'].format(user_data.get('id'))
        return user_data


class PersonaLogin(ILoginProvider):
    """
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
                                success: function(res, status, xhr) { window.location.reload(); },
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
            if response.ok and response.json()['status'] == 'okay':
                return ProviderToken(self.name, response.json()['email'])
            raise LoginProviderException(response.content)
        #raise LoginProviderException('no assertion provided')

    def aquire_additional_user_details(self, provider_token):
        return dict(
            avatar_img='http://www.gravatar.com/avatar/{0}'.format(
                hashlib.md5(provider_token.token.encode('utf-8')).hexdigest()
            )
        )
