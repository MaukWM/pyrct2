"""Integration tests for game.paths high-level API."""

import pytest

from pyrct2._generated.enums import Direction
from pyrct2._generated.objects import RideObjects
from pyrct2.errors import ActionError
from pyrct2.world._tile import Tile


def test_place_path(game):
    game.park.cheats.build_in_pause_mode()
    result = game.paths.place(Tile(10, 10))
    assert result.cost > 0

    tile = game.world.get_tile(Tile(10, 10))
    assert len(tile.paths) == 1


def test_place_path_auto_connects(game):
    """Place a 2x2 square and verify all edges connect correctly.

    Layout:        Edge bits: bit0=W, bit1=S, bit2=E, bit3=N
      NW  NE
      SW  SE
    """
    game.park.cheats.build_in_pause_mode()
    # NW, NE, SW, SE
    game.paths.place(Tile(10, 10))
    game.paths.place(Tile(11, 10))
    game.paths.place(Tile(10, 11))
    game.paths.place(Tile(11, 11))

    nw = game.world.get_tile(Tile(10, 10)).paths[0].edges
    ne = game.world.get_tile(Tile(11, 10)).paths[0].edges
    sw = game.world.get_tile(Tile(10, 11)).paths[0].edges
    se = game.world.get_tile(Tile(11, 11)).paths[0].edges

    # NW: east + south
    assert nw & 0b0100, "NW should have east edge"
    assert nw & 0b0010, "NW should have south edge"
    # NE: west + south
    assert ne & 0b0001, "NE should have west edge"
    assert ne & 0b0010, "NE should have south edge"
    # SW: east + north
    assert sw & 0b0100, "SW should have east edge"
    assert sw & 0b1000, "SW should have north edge"
    # SE: west + north
    assert se & 0b0001, "SE should have west edge"
    assert se & 0b1000, "SE should have north edge"


def test_place_queue_path(game):
    game.park.cheats.build_in_pause_mode()
    game.paths.place(Tile(10, 10), queue=True)

    path = game.world.get_tile(Tile(10, 10)).paths[0]
    assert path.isQueue is True


# ── Failure modes ────────────────────────────────────────────────────


def test_place_path_blocked_by_stall(game):
    """Can't place a path where a stall is."""
    game.park.cheats.build_in_pause_mode()
    game.rides.place_stall(
        obj=RideObjects.stall.BALLOON_STALL,
        tile=Tile(20, 20),
        direction=Direction.NORTH,
    )
    with pytest.raises(ActionError):
        game.paths.place(Tile(20, 20))


def test_place_path_blocked_by_flat_ride(game):
    """Can't place a path where a flat ride is."""
    game.park.cheats.build_in_pause_mode()
    game.rides.place_flat_ride(
        obj=RideObjects.gentle.MERRY_GO_ROUND,
        tile=Tile(20, 20),
        entrance=Tile(22, 21),
        exit=Tile(22, 19),
        direction=Direction.NORTH,
    )
    with pytest.raises(ActionError):
        game.paths.place(Tile(20, 20))


def test_place_path_out_of_bounds(game):
    """Can't place a path outside the map."""
    game.park.cheats.build_in_pause_mode()
    with pytest.raises(ActionError):
        game.paths.place(Tile(999, 999))


def test_place_path_below_ground(game):
    """Can't place a path below ground level."""
    game.park.cheats.build_in_pause_mode()
    with pytest.raises(ValueError, match="below the surface"):
        game.paths.place(Tile(10, 10), height=0)


def test_place_path_idempotent(game):
    """Placing the same path twice is a no-op (cost=0)."""
    game.park.cheats.build_in_pause_mode()
    r1 = game.paths.place(Tile(10, 10))
    assert r1.cost > 0
    r2 = game.paths.place(Tile(10, 10))
    assert r2.cost == 0


# ── Removal ──────────────────────────────────────────────────────────


def test_remove_path(game):
    game.park.cheats.build_in_pause_mode()
    game.paths.place(Tile(10, 10))
    assert len(game.world.get_tile(Tile(10, 10)).paths) == 1

    game.paths.remove(Tile(10, 10))
    assert len(game.world.get_tile(Tile(10, 10)).paths) == 0


def test_remove_path_no_path(game):
    """Removing where there's no path raises ActionError."""
    game.park.cheats.build_in_pause_mode()
    with pytest.raises(ActionError):
        game.paths.remove(Tile(10, 10))


def test_remove_path_at_height(game):
    """Remove an elevated path, leaving ground-level path intact."""
    game.park.cheats.build_in_pause_mode()
    game.paths.place(Tile(10, 10))
    # Ground is at 7 land steps (z=112), clearance at 9. Place above clearance.
    game.paths.place(Tile(10, 10), height=9)
    assert len(game.world.get_tile(Tile(10, 10)).paths) == 2

    game.paths.remove(Tile(10, 10), height=9)
    paths = game.world.get_tile(Tile(10, 10)).paths
    assert len(paths) == 1
    assert paths[0].baseZ == game.world.get_tile(Tile(10, 10)).surface.baseZ


def test_remove_path_ground_keeps_elevated(game):
    """Removing without height removes ground-level path, keeps elevated."""
    game.park.cheats.build_in_pause_mode()
    game.paths.place(Tile(10, 10))
    game.paths.place(Tile(10, 10), height=9)
    assert len(game.world.get_tile(Tile(10, 10)).paths) == 2

    game.paths.remove(Tile(10, 10))
    paths = game.world.get_tile(Tile(10, 10)).paths
    assert len(paths) == 1
    assert paths[0].baseZ > game.world.get_tile(Tile(10, 10)).surface.baseZ
