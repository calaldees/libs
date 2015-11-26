import pytest

# Pytest commandline handling --------------------------------------------------

def pytest_addoption(parser):
    parser.addoption("--noserver", action="store_true", help="Do not instantiate local python socket server for tests.")


def pytest_runtest_setup(item):
    pass
    try:
        noserver = item.config.getoption("--noserver")
    except ValueError:
        noserver = False
