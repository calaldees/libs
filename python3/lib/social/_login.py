
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
            return dict(facebook_dialog_url=facebook_dialog_url)

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
        user_data['avatar'] = facebook.endpoints['avatar'].format(user_data.get('id'))
        return user_data
