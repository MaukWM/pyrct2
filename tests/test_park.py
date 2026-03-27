"""Integration tests for game.park high-level API.

Tests run against tests/fixtures/test_scenario.park — a fresh empty park
named "Test Park", closed, rating 0, value 0, starting year 1 month 0 day 1.
"""

import pytest


def test_park_name(game):
    assert game.park.name == "Test Park"


def test_park_rating(game):
    assert game.park.rating == 0


def test_park_value(game):
    assert game.park.value == 0


def test_park_is_open(game):
    assert game.park.is_open is False


def test_park_date(game):
    d = game.park.date
    assert d.year == 1
    assert d.month == 0
    assert d.day == 1


def test_set_name(game):
    game.park.set_name("Renamed Park")
    assert game.park.name == "Renamed Park"


def test_open_close(game):
    assert game.park.is_open is False
    game.park.open()
    assert game.park.is_open is True
    game.park.close()
    assert game.park.is_open is False


@pytest.mark.xfail(
    reason="OpenRCT2 omits ScenarioObjective.length for guestsBy objectives. "
    "See docs/openrct2-api-bugs.md #1. Expected to be fixed upstream.",
    raises=Exception,
)
def test_park_objective(game):
    obj = game.park.objective
    assert obj is not None
    # TODO: Test this once upstream is fixed
