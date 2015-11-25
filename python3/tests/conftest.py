import pytest

import logging
log = logging.getLogger(__name__)


def pytest_addoption(parser):
    parser.addoption("--noserver", action="store_true", help="Do not instantiate local python socket server for tests.")
def pytest_runtest_setup(item):
    try:
        noserver = item.config.getoption("--noserver")
    except ValueError:
        noserver = False


@pytest.fixture(scope='function')
def echo_server(request):
    if request.config.getoption("--noserver"):
        return

    from lib.multisocket.multisocket_server import EchoServerManager
    echo_server = EchoServerManager(tcp_port=9872)
    echo_server.start()

    def finalizer():
        echo_server.stop()
    request.addfinalizer(finalizer)

    return echo_server


@pytest.fixture(scope='function')
def subscription_server(request):
    if request.config.getoption("--noserver"):
        return

    from lib.multisocket.subscription_echo_server import SubscriptionEchoServerManager
    subscription_server = SubscriptionEchoServerManager(tcp_port=9872)
    subscription_server.start()

    def finalizer():
        subscription_server.stop()
    request.addfinalizer(finalizer)

    return subscription_server
