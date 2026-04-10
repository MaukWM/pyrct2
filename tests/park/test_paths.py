"""Integration tests for game.paths high-level API."""

import pytest

from pyrct2._generated.enums import Direction, EdgeBit
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

    Layout:
      NW  NE
      SW  SE
    """
    game.park.cheats.build_in_pause_mode()
    game.paths.place(Tile(10, 10))
    game.paths.place(Tile(11, 10))
    game.paths.place(Tile(10, 11))
    game.paths.place(Tile(11, 11))

    nw = game.world.get_tile(Tile(10, 10)).paths[0].edges
    ne = game.world.get_tile(Tile(11, 10)).paths[0].edges
    sw = game.world.get_tile(Tile(10, 11)).paths[0].edges
    se = game.world.get_tile(Tile(11, 11)).paths[0].edges

    assert nw & EdgeBit.EAST, "NW should have east edge"
    assert nw & EdgeBit.SOUTH, "NW should have south edge"
    assert ne & EdgeBit.WEST, "NE should have west edge"
    assert ne & EdgeBit.SOUTH, "NE should have south edge"
    assert sw & EdgeBit.EAST, "SW should have east edge"
    assert sw & EdgeBit.NORTH, "SW should have north edge"
    assert se & EdgeBit.WEST, "SE should have west edge"
    assert se & EdgeBit.NORTH, "SE should have north edge"


def test_place_queue_path(game):
    game.park.cheats.build_in_pause_mode()
    game.paths.place(Tile(10, 10), queue=True)

    path = game.world.get_tile(Tile(10, 10)).paths[0]
    assert path.isQueue is True
    # Verify a queue surface was auto-selected
    surfaces = game._query("get_objects", {"type": "footpath_surface"})
    surface_id = next(s["identifier"] for s in surfaces if s["index"] == path.surfaceObject)
    assert "queue" in surface_id, f"expected queue surface, got {surface_id}"


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


# ── Slopes ───────────────────────────────────────────────────────────


def test_place_slope(game):
    """Place a sloped path and verify it's sloped in the right direction."""
    game.park.cheats.build_in_pause_mode()
    game.paths.place(Tile(10, 10), slope=Direction.EAST)

    path = game.world.get_tile(Tile(10, 10)).paths[0]
    assert path.slopeDirection == Direction.EAST
    # Sloped clearance = baseZ + kPathClearance(32) + kPathHeightStep(16) = baseZ + 48
    assert path.clearanceZ == path.baseZ + 48


def test_slope_auto_connects_flat_to_flat(game):
    """flat → slope → flat(higher) auto-connects end-to-end.

    slope=Direction.EAST means: low end is west, high end is east.
    The flat path west of the slope is at the same height.
    The flat path east of the slope is one land step higher.
    """
    game.park.cheats.build_in_pause_mode()
    game.paths.place(Tile(10, 10))                          # flat (low side)
    game.paths.place(Tile(11, 10), slope=Direction.EAST)    # slope rising east
    game.paths.place(Tile(12, 10), height=8)                # flat (high side, +1 step)

    low = game.world.get_tile(Tile(10, 10)).paths[0]
    slope = game.world.get_tile(Tile(11, 10)).paths[0]
    high = game.world.get_tile(Tile(12, 10)).paths[0]

    assert low.edges & EdgeBit.EAST, "low should connect east to slope"
    assert slope.edges & EdgeBit.WEST, "slope should connect west to low"
    assert slope.edges & EdgeBit.EAST, "slope should connect east to high"
    assert high.edges & EdgeBit.WEST, "high should connect west to slope"


def test_slope_no_perpendicular_connection(game):
    """Slopes don't connect sideways — only along their axis."""
    game.park.cheats.build_in_pause_mode()
    game.paths.place(Tile(10, 10), slope=Direction.EAST)    # slope east
    game.paths.place(Tile(10, 11))                          # flat south

    slope = game.world.get_tile(Tile(10, 10)).paths[0]
    flat = game.world.get_tile(Tile(10, 11)).paths[0]

    assert slope.edges == 0, "slope should have no edges (no along-axis neighbors)"
    assert flat.edges == 0, "flat should have no edges (perpendicular to slope)"


def test_slope_staircase(game):
    """Multiple slopes in sequence form a staircase."""
    game.park.cheats.build_in_pause_mode()
    # 3 slopes going east, each one land step higher
    for i in range(3):
        game.paths.place(Tile(10 + i, 10), slope=Direction.EAST, height=7 + i)

    # Middle slope should connect both ways
    middle = game.world.get_tile(Tile(11, 10)).paths[0]
    assert middle.edges & EdgeBit.WEST, "middle slope connects west (down)"
    assert middle.edges & EdgeBit.EAST, "middle slope connects east (up)"


def test_slope_removal_uses_base_z(game):
    """Removing a slope uses its baseZ (lower end), not topZ."""
    game.park.cheats.build_in_pause_mode()
    game.paths.place(Tile(10, 10), slope=Direction.EAST)

    # Default removal (ground level) should work — baseZ is ground level
    game.paths.remove(Tile(10, 10))
    assert len(game.world.get_tile(Tile(10, 10)).paths) == 0


def test_slope_queue(game):
    """Queue paths work on slopes."""
    game.park.cheats.build_in_pause_mode()
    game.paths.place(Tile(10, 10), slope=Direction.EAST, queue=True)

    path = game.world.get_tile(Tile(10, 10)).paths[0]
    assert path.isQueue is True
    assert path.slopeDirection == Direction.EAST
