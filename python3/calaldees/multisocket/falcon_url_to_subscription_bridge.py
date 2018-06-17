
# @view_config(route_name='event')
# def event(request):
#     """
#     Take GET/POST application/x-form or application/json
#     Normalize the input
#     push to websocket
#     Commandline example:
#         curl -XGET http://localhost:6543/event/screen_size.set -d '{"deviceid": "main", "top":"100px", "left":"100px", "width": "400px", "height":"300px"}'
#     """
#     cmd = {}
#     cmd.update(request.matchdict)
#     cmd.update(request.params)
#     try:
#         cmd.update(json.loads(request.text))
#     except json.decoder.JSONDecodeError:
#         pass
#     if cmd:
#         cmd = {'action': 'message', 'data': [cmd]}
#         log.debug("remote command - {0}".format(cmd))
#         request.registry['socket_manager'].recv(json.dumps(cmd).encode('utf8'))
#     return Response()


class URLtoSubscriptionServerBridge:
    #def __init__(self):
    #    pass

    def on_get(self, req, resp):
        #req.get_param('param')
        resp.media = ['test']

    def on_post(self, req, resp):
        resp.media = {
            'test': 'a'
        }
        resp.status = falcon.HTTP_200


# Setup App -------------------------------------------------------------------

def setup_falcon_app(**kwargs)
    import falcon
    app = falcon.API()
    app.add_route('/', URLtoSubscriptionServerBridge())


# Commandlin Args -------------------------------------------------------------

def get_args():
    import argparse

    parser = argparse.ArgumentParser(
        prog=__name__,
        description='''
        ''',
    )

    parser.add_argument('--host', action='store', default='0.0.0.0', help='')
    parser.add_argument('--port', action='store', default=8000, type=int, help='')

    parser.add_argument('--subscription_server_tcp_port', action='store', default=9872, type=int, help='')

    kwargs = vars(parser.parse_args())
    return kwargs


# Main ------------------------------------------------------------------------

if __name__ == '__main__':
    kwargs = get_args()

    from wsgiref import simple_server
    httpd = simple_server.make_server(kwargs['host'], kwargs['port'], setup_falcon_app(**kwargs))
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
