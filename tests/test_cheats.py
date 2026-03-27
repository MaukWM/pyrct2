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
    if not name.startswith("_")
    and name != "list"
    and list(inspect.signature(method).parameters.keys()) == ["self"]
]


@pytest.mark.parametrize("method", ONE_SHOT_CHEATS)
def test_one_shot_cheat(game, method):
    getattr(game.park.cheats, method)()
