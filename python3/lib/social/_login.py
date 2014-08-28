import hashlib
import requests

from collections import namedtuple

ProviderToken = namedtuple('ProviderToken', ['provider', 'token'])

from . import facebook


class LoginProvider(object):
    """
    Not needed, but here to document the methods a LoginProvider should implement
    """

    def __init__(self):
        pass

    def display_login_dialog(request):
        """
        Should check if the required state is present to show dialog
        Then return dict with details for this provider for the template to render
        """
        return False

    def verify_cridentials(request):
        """
        Returns a ProviderToken
        """
        return None

    def aquire_additional_user_details(provider_token):
        """
        """
        return {}


class LoginProviderException(Exception):
    failed_to_verify_cridentials = 1


class FacebookLogin(LoginProvider):

    def display_login_dialog(request):
        if not request.params.get('code'):
            facebook_dialog_url = facebook.login_dialog_url(
                appid=request.registry.settings.get('facebook.appid'),
                csrf_token=request.session['csrf_token'],
                permissions=request.registry.settings.get('facebook.permissions'),
                redirect_uri=request.path_url,
            )
            return dict(redirect_url=facebook_dialog_url)

    def verify_cridentials(request):
        if request.params.get('code') and request.params.get('state'):
            if request.params.get('state') != request.session.get('csrf_token'):
                raise LoginProviderException('csrf mismatch')  # 400
            # Check submited code with facebook
            response = facebook.call_api(
                'oauth/access_token',
                client_id     = request.registry.settings.get('facebook.appid'),
                client_secret = request.registry.settings.get('facebook.secret'),
                redirect_uri  = request.path_url,
                code          = request.params.get('code'),
            )
            if response.get('error'):
                raise LoginProviderException(response.get('error'))
            return ProviderToken('facebook', response.get('access_token'))

    def aquire_additional_user_details(provider_token):
        fb = facebook.facebook(access_token=provider_token.token)
        user_data = fb.api('me')
        user_data['avatar_img'] = facebook.endpoints['avatar'].format(user_data.get('id'))
        return user_data


class PersonaLogin(LoginProvider):
    """
    https://developer.mozilla.org/en-US/Persona/Quick_Setup
    """

    def html_include():
        """
        Rather than having to edit multiple static js files and headers
        Keep all js and server flow in one place
        Slightly fugly having js/html in a py file, but there are benefits

        'currentUserEmail' needs to be set previously in the js for this to function
        """
        return """
            <script src="https://login.persona.org/include.js"></script>
            <script type="text/javascript">
                navigator.id.watch({
                    loggedInUser: currentUserEmail,
                    onlogin: function(assertion) {
                        $.ajax({
                            type: 'POST',
                            url: '/auth/login',
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
                            url: '/auth/logout',
                            success: function(res, status, xhr) { window.location.reload(); },
                            error: function(xhr, status, err) { alert("Logout failure: " + err); }
                        });
                    }
                });
            </script>
        """

    def display_login_dialog(request):
        if not request.params.get('assertion'):
            #facebook_dialog_url = facebook.login_dialog_url(
            #    appid=request.registry.settings.get('facebook.appid'),
            ##    csrf_token=request.session['csrf_token'],
            #    permissions=request.registry.settings.get('facebook.permissions'),
            #    redirect_uri=request.path_url,
            #)
            return dict(run_js='navigator.id.request();')

    def verify_cridentials(request):
        if request.params.get('assertion'):
            "assertion=<ASSERTION>&audience=https://example.com:443" "https://verifier.login.persona.org/verify"
            response = requests.post(
                'https://verifier.login.persona.org/verify',
                data={
                    'assertion': request.params.get('assertion'),
                    'audience': request.registry.settings.get('server.url')
                },
                verify=True
            )
            if response.ok and response.json['status'] == 'okay':
                return ProviderToken('persona', response.json['email'])
        raise LoginProviderException(response.content)


    def aquire_additional_user_details(provider_token):
        return dict(
            avatar_img='http://www.gravatar.com/avatar/{0}'.format(
                hashlib.md5(provider_token.encode('utf-8')).hexdigest()
            )
        )