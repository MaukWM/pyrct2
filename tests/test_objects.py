"""Integration tests for game.objects proxy."""

from pyrct2._generated.objects import RideObjects
from pyrct2.errors import QueryError


def test_is_loaded_preloaded(game):
    """Merry-Go-Round is preloaded in the test scenario."""
    assert game.objects.is_loaded(RideObjects.gentle.MERRY_GO_ROUND)


def test_is_loaded_not_present(game):
    """Dodgems is not preloaded in the test scenario."""
    assert not game.objects.is_loaded(RideObjects.gentle.BUMPER_CARS)


def test_get_loaded_object(game):
    """get() succeeds for a loaded object."""
    info = game.objects.get(RideObjects.gentle.MERRY_GO_ROUND)
    assert "index" in info


def test_load_idempotent(game):
    """Loading an already-loaded object returns the same index."""
    obj = RideObjects.gentle.MERRY_GO_ROUND
    info1 = game.objects.get(obj)
    game.objects.load(obj)
    info2 = game.objects.get(obj)
    assert info1["index"] == info2["index"]


def test_get_not_loaded_raises(game):
    """get() raises QueryError for an unloaded object."""
    import pytest

    with pytest.raises(QueryError):
        game.objects.get(RideObjects.gentle.BUMPER_CARS)


def test_load_unload_all_ride_objects(game):
    """Every ride object in the catalog can be loaded and unloaded."""
    all_objects = RideObjects.all()
    assert len(all_objects) > 100

    for obj in all_objects:
        game.objects.load(obj)
        assert game.objects.is_loaded(obj), f"Failed to load {obj.identifier}"

        game.objects.unload(obj)
        assert not game.objects.is_loaded(obj), f"Failed to unload {obj.identifier}"
