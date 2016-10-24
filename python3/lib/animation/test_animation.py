import pytest

from .timeline import Timeline


@pytest.fixture()
def timeline():
    return Timeline()


def test_timeline_creation(timeline):
    pass
