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


@pytest.fixture(scope="session")
def echo_server(request):
    from lib.multisocket.multisocket_server import EchoServerManager
    manager = EchoServerManager(tcp_port=9872)
    manager.start()

    def finalizer():
        manager.stop()
    request.addfinalizer(finalizer)

    return manager
