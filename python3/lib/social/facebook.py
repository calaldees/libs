## -*- coding: utf-8 -*-

import json
from urllib.parse import urlencode
from urllib.request import urlopen, HTTPError

endpoints = dict(
    service='http://graph.facebook.com/',
    avatar='https://graph.facebook.com/{0}/picture',
    app_setup='https://developers.facebook.com/apps/{0}/summary',
    auth='https://www.facebook.com/dialog/oauth?{0}',
)


# Base api call request handling -----------------------------------------------

def call_api(service_path, *args, **kwargs):
    """
    Call Facebook API function

    Because the facebook API returns differnt return types, this util method attempts to unify them.
    the POST or GET can be controled my passing '_method' in kwargs - default is GET
    """
    # Service
    service_url = endpoints['service']
    service_url += service_path

    # Secure
    if kwargs.pop('secure', True) or 'access_token' in kwargs or 'client_secret' in kwargs:  # Facebook will reject any request made with an access token if https is not enabled
        service_url = service_url.replace('http:', 'https:')

    # Method - prepare arguments for GET or POST
    data = None
    if kwargs:
        method = kwargs.pop('_method', 'GET').upper()
        data = urlencode(kwargs)
        # Append kwargs to query string if GET request
        if method == 'GET':
            service_url += "?%s" % data
            data = None

    # Make Call
    try:
        http_response = urlopen(service_url,data)
        response = http_response.read()
        #http_response.close()
    except HTTPError as http_response_error:
        response = http_response_error.read()
        # close needed?
    response = response.decode('utf-8')

    # Attempt decode and return response JSON
    try:
        return json.loads(response)
    except ValueError:
        pass

    # Attempt decode split('&') of data
    #   Facebook can return it's own URL style string as a response to an API call
    try:
        response_vars = {}
        for response_var in response.split('&'):
            key, value = tuple(response_var.split('='))
            response_vars[key] = value
        return response_vars
    except:
        pass

    # Unable to decode response
    return response


# Facebook object --------------------------------------------------------------

class facebook():
    """
    Simple object to cleanly keep track of facebook access token for app or user
    Can also queue and execute Batch requests and FQL

    Examples:
        fb = facebook(access_token='usertoken')
        fb.api_queue('me')
        fb.api_queue('me/feed', limit=3)
        user, stream = tuple(fb.api_batch())
        print(user['first_name'])
        print(stream['data'])

        or

        fb = facebook(access_token='apptoken', appid='xxx')
        or
        fb = facebook(appid='xxx', secret='xxx')
        test_users = fb.api('{appid}/accounts/test-users')
    """
    def __init__(self, access_token=None, appid=None, secret=None, secure=True):
        """
        access_token
        or
        appid and secret (if used for aquireing app access_token)
        """
        self.overlay_path = {}  # appid is sometimes used request paths (and potentially other details in a facebook request), this dict is {format_name} formatted over the service_path on each request
        self.overlay_fields = {}  # added to every api request made via this object
        self.batch = []

        if appid:
            self.overlay_path['appid'] = appid
        if secret and not access_token:
            # Authenticate as the Facebook App - https://developers.facebook.com/docs/authentication/applications/
            access_token = call_api('oauth/access_token', client_id=appid, client_secret=secret, grant_type='client_credentials')['access_token']

        self.overlay_fields.update({'access_token': access_token, 'secure': secure})

    def api(self, service_path, *args, **kwargs):
        """
        Single facebook api call.
        will automatically:
            - replace any '{appid}' in the service path
            - add access_token to the request
        """
        service_path = service_path.format(self.overlay_path)
        api_args = dict(self.overlay_fields)
        api_args.update(kwargs)
        return call_api(service_path, *args, **api_args)

    def api_queue(self, service_path, *args, **kwargs):
        """
        Queue an api request to be sent by api_batch
        """
        service_path = service_path.format(self.overlay_path)
        method = kwargs.pop('_method', 'GET').upper()
        data = urlencode(kwargs)
        if method == 'GET':
            self.batch.append({'method': method, 'relative_url': '{0}?{1}'.format(service_path, data)})
        else:
            self.batch.append({'method': method, 'relative_url': service_path, 'body': data})

    def api_batch(self, decode_json=True):
        """
        Send api_queue calls as one http batch request
        https://developers.facebook.com/docs/reference/api/batch/
        """
        if not self.batch:
            return []
        api_args = dict(self.overlay_fields)
        api_args.update({'batch': json.dumps(self.batch), '_method': 'POST'})
        self.batch = []
        data = call_api('', **api_args)
        if decode_json:
            data = [json.loads(item['body']) for item in data]
        return tuple(data)

    def fql(self, query):
        """
        https://developers.facebook.com/docs/reference/fql/
        """
        if isinstance(query, dict):
            query = json.dumps(query)
        return self.api('fql', q=query)


# Utils ------------------------------------------------------------------------

def login_dialog_url(appid, csrf_token, redirect_uri, permissions=None):
    """
        permisions: comma separated string
    """
    kwargs = dict(
        client_id=appid,
        state=csrf_token,
        redirect_uri=redirect_uri,
    )
    if permissions:
        kwargs['scope'] = permissions
    return endpoints['auth'].format(urlencode(kwargs))
