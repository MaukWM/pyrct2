"""Integration tests for game.park.research high-level API.

Fixture state: funding=2 (NORMAL), all 7 priority categories enabled,
stage='initial_research', progress=0, 16 invented, 9 uninvented.
"""


def test_funding(game):
    assert game.park.research.funding == 2


def test_priorities(game):
    assert game.park.research.priorities == [
        "transport", "gentle", "rollercoaster", "thrill", "water", "shop", "scenery"
    ]


def test_stage(game):
    assert game.park.research.stage == "initial_research"


def test_progress(game):
    assert game.park.research.progress == 0


def test_invented_items(game):
    assert len(game.park.research.invented_items) == 16


def test_uninvented_items(game):
    assert len(game.park.research.uninvented_items) == 9


def test_expected_item(game):
    assert game.park.research.expected_item is None


def test_last_researched_item(game):
    assert game.park.research.last_researched_item is None
