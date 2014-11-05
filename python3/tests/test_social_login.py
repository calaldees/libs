from unittest.mock import Mock
from pyramid.testing import DummyRequest

from lib.pyramid_helpers.auto_format import action_error

from lib.social._login import ProviderToken
from lib.social.social_login import SocialLogin

# TODO
#  Test multiple providers
#  Test html_include


def test_logout():
    request = DummyRequest()
    request.session['user'] = {'a': 1}
    SocialLogin().logout(request)
    assert not request.session.get('user'), 'The user should have been removed from the session'


def test_login_step1_login_dialog():
    request = DummyRequest()
    login_provider = Mock()
    login_provider.name = 'test_provider'
    user_store = Mock()

    login_provider.login_dialog_data = lambda request: {'dialog_instructions': 'redirect_or_something'}

    response = SocialLogin().login(request, login_provider, user_store)

    assert response.get('status') == 'ok'
    assert request.session.get('csrf_token')
    assert response['data']['login_providers']['test_provider'] == {'dialog_instructions': 'redirect_or_something'}


def test_login_step2_verify_cridentials_fail():
    request = DummyRequest(params={'user_lookup_token': 'user_lookup_token'})
    login_provider = Mock()
    login_provider.name = 'test_provider'
    user_store = Mock()

    login_provider.verify_cridentials.return_value = None

    try:
        response = SocialLogin().login(request, login_provider, user_store)
    except action_error as ae:
        response = ae.d

    assert response.get('status') == 'error'


def test_login_step2_verify_cridentials_success_and_user_exists():
    request = DummyRequest(params={'user_lookup_token': 'user_lookup_token'})
    login_provider = Mock()
    login_provider.name = 'test_provider'
    user_store = Mock()

    mock_user = Mock()
    mock_user.name = 'test_username'

    login_provider.verify_cridentials.side_effect = lambda request: ProviderToken(provider='test_provider', token=request.params.get('user_lookup_token') + '+verified_by_external_provider', response={})
    user_store.get_user_from_token.side_effect = lambda provider_token: mock_user
    user_store.user_to_session_dict.side_effect = lambda user: {'name': user.name, 'admin': True}

    response = SocialLogin().login(request, login_provider, user_store)

    assert response.get('status') == 'ok'
    assert request.session['user']['name'] == 'test_username'

    login_provider.verify_cridentials.assert_called_with(request)
    user_store.get_user_from_token.assert_called_with(ProviderToken(provider='test_provider', token='user_lookup_token+verified_by_external_provider', response={}))


def test_login_step2_verify_cridentials_success_and_user_not_exists():
    request = DummyRequest(params={'user_lookup_token': 'user_lookup_token'})
    login_provider = Mock()
    login_provider.name = 'test_provider'
    user_store = Mock()

    mock_created_user = Mock()

    login_provider.verify_cridentials.side_effect = lambda request: ProviderToken(provider='test_provider', token=request.params.get('user_lookup_token') + '+verified_by_external_provider', response={})
    user_store.get_user_from_token.side_effect = [None, mock_created_user]  # The fist time no user found, the second time the user object is returned (this is because create_user has been run)
    login_provider.aquire_additional_user_details.side_effect = lambda provider_token: {'name': provider_token.token + '+user_data'}
    def create_user(provider_token, **user_data):
        for k, v in user_data.items():
            setattr(mock_created_user, k, v)
    user_store.create_user.side_effect = create_user
    user_store.user_to_session_dict.side_effect = lambda user: {'name': user.name, 'admin': True}

    response = SocialLogin().login(request, login_provider, user_store)

    assert response.get('status') == 'ok'
    assert request.session['user']['name'] == 'user_lookup_token+verified_by_external_provider+user_data'
