import pytest
from multiprocessing import Process

# Pytest commandline handling --------------------------------------------------

def pytest_addoption(parser):
    parser.addoption("--noserver", action="store_true", help="Do not instantiate local python socket server for tests.")


def pytest_runtest_setup(item):
    pass
    try:
        noserver = item.config.getoption("--noserver")
    except ValueError:
        noserver = False



@pytest.fixture(scope='session')
def http_server(request):
    import http.server
    import socketserver

    server = http.server.HTTPServer(('', 8000), http.server.SimpleHTTPRequestHandler)

    server_thread = Process(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    def finalizer():
        # http://stackoverflow.com/questions/22171441/shutting-down-python-tcpserver-by-custom-handler
        # https://searchcode.com/codesearch/view/22865337/
        server_thread.terminate()
        server_thread.join()
    request.addfinalizer(finalizer)

    return server


@pytest.fixture(scope='session')
def browser(request):
    from selenium import webdriver
    driver = webdriver.PhantomJS()  # executable_path=''
    driver.set_window_size(1120, 550)
    def finalizer():
        driver.quit()
    request.addfinalizer(finalizer)
    return driver
