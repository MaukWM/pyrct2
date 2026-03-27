"""Integration tests for game.park.cheats high-level API.

Fixture state: all boolean cheats False, forcedParkRating -1.
"""

import inspect

import pytest

from pyrct2.park._cheats import CheatsProxy

# Boolean toggle methods all have signature (self, active: bool = True).
# Discover them by inspecting parameters — future value/one-shot methods
# will have different signatures and won't match.
BOOLEAN_CHEATS = [
    name
    for name, method in inspect.getmembers(CheatsProxy, predicate=inspect.isfunction)
    if not name.startswith("_")
    and name != "list"
    and list(inspect.signature(method).parameters.keys()) == ["self", "active"]
]


def test_list_all_off(game):
    cheats = game.park.cheats.list()
    assert cheats.sandboxMode is False
    assert cheats.buildInPauseMode is False
    assert cheats.freezeWeather is False


@pytest.mark.parametrize("method", BOOLEAN_CHEATS)
def test_boolean_cheat_toggle(game, method):
    before = game.park.cheats.list().model_dump()
    getattr(game.park.cheats, method)()
    after = game.park.cheats.list().model_dump()
    assert before != after, f"{method}() had no effect"

    getattr(game.park.cheats, method)(active=False)
    restored = game.park.cheats.list().model_dump()
    assert restored == before, f"{method}(active=False) did not restore state"


# One-shot methods have signature (self) only — no parameters.
ONE_SHOT_CHEATS = [
    name
    for name, method in inspect.getmembers(CheatsProxy, predicate=inspect.isfunction)
    if not name.startswith("_") and name != "list" and list(inspect.signature(method).parameters.keys()) == ["self"]
]


@pytest.mark.parametrize("method", ONE_SHOT_CHEATS)
def test_one_shot_cheat(game, method):
    getattr(game.park.cheats, method)()


# -- Value cheats --


def test_set_forced_park_rating(game):
    game.park.cheats.set_forced_park_rating(500)
    assert game.park.cheats.list().forcedParkRating == 500
    game.park.cheats.set_forced_park_rating(-1)
    assert game.park.cheats.list().forcedParkRating == -1


def test_set_money(game):
    game.park.cheats.set_money(999999)
    assert game.park.finance.cash == 999999


def test_add_money(game):
    original = game.park.finance.cash
    game.park.cheats.add_money(50000)
    assert game.park.finance.cash == original + 50000


def test_clear_loan(game):
    game.park.cheats.clear_loan()
    assert game.park.finance.loan == 0


def test_generate_guests(game):
    game.park.cheats.generate_guests(10)


def test_force_weather(game):
    game.park.cheats.force_weather(3)  # rain


def test_set_grass_length(game):
    game.park.cheats.set_grass_length(1)


def test_set_staff_speed(game):
    game.park.cheats.set_staff_speed(255)


def test_give_all_guests(game):
    game.park.cheats.give_all_guests(2)  # BALLOON (OBJECT_* enum: 0=money, 1=map, 2=balloon, 3=umbrella)
