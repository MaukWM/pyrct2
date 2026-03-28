"""Unit tests for Tile coordinate type — no game instance needed."""

from pyrct2.world import TILE_SIZE, Tile


def test_to_world():
    assert Tile(x=5, y=10).to_world() == (160, 320)


def test_from_world_floors():
    """Mid-tile world coords floor to the tile."""
    assert Tile.from_world(176, 336) == Tile(x=5, y=10)
    assert Tile.from_world(191, 351) == Tile(x=5, y=10)
    assert Tile.from_world(192, 352) == Tile(x=6, y=11)


def test_roundtrip():
    """Tile -> world -> Tile preserves coordinates."""
    original = Tile(x=48, y=31)
    assert Tile.from_world(*original.to_world()) == original


def test_distance_to():
    assert Tile(x=0, y=0).distance_to(Tile(x=3, y=4)) == 7


def test_frozen_hashable():
    """Frozen Tiles work as dict keys and in sets."""
    t = Tile(x=5, y=10)
    assert {t, Tile(x=5, y=10)} == {t}
    assert {t: "a"}[Tile(x=5, y=10)] == "a"
