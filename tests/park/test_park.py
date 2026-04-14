"""Integration tests for game.park high-level API.

Tests run against tests/fixtures/test_scenario.park — a fresh empty park
named "Test Park", closed, rating 0, value 0, starting year 1 month 0 day 1.
"""

import pytest

from pyrct2.world import Tile


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


# ── Park entrances ───────────────────────────────────────────────────


def test_park_entrance(game):
    """Test scenario has one park entrance with expected tiles and arrival tile."""
    entrances = game.park.entrances
    assert len(entrances) == 1

    entrance = entrances[0]
    assert len(entrance.tiles) == 3
    assert Tile(49, 30) in entrance.tiles
    assert Tile(49, 29) in entrance.tiles
    assert Tile(49, 31) in entrance.tiles

    # arrival_tile is the owned tile just inside the gate
    assert entrance.arrival_tile == Tile(48, 30)
    td = game.world.get_tile(entrance.arrival_tile)
    assert td.surface.hasOwnership is True


@pytest.mark.xfail(
    reason="OpenRCT2 omits ScenarioObjective.length for guestsBy objectives. "
    "See docs/openrct2-api-bugs.md #1. Expected to be fixed upstream.",
    raises=Exception,
)
def test_park_objective(game):
    obj = game.park.objective
    assert obj is not None
    # TODO: Test this once upstream is fixed
