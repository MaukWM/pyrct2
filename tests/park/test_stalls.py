"""Integration tests for game.rides.place_stall()."""

import pytest

from pyrct2._generated.enums import Direction
from pyrct2._generated.objects import RideObjects
from pyrct2.park._rides import _require_stall
from pyrct2.world import Tile


# ── Validation (pure, no game needed) ────────────────────────────────


def test_require_stall_accepts_stall():
    """A stall object passes validation."""
    _require_stall(RideObjects.stall.BURGER_BAR)  # should not raise


def test_require_stall_rejects_ride():
    """A non-stall object raises ValueError."""
    with pytest.raises(ValueError, match="not a stall"):
        _require_stall(RideObjects.gentle.MERRY_GO_ROUND)


# ── Integration tests ────────────────────────────────────────────────


def test_place_stall_open_close(game):
    """Open and close a stall, verifying status transitions."""
    game.park.cheats.build_in_pause_mode()

    stall = game.rides.place_stall(
        obj=RideObjects.stall.BURGER_BAR,
        tile=Tile(20, 20),
    )
    # Verify track on the tile
    tile_data = game.world.get_tile(Tile(20, 20))
    assert len(tile_data.tracks) > 0

    # Starts closed
    assert stall.data.status == "closed"

    # Open
    stall.open()
    stall.refresh()
    assert stall.data.status == "open"

    # Close
    stall.close()
    stall.refresh()
    assert stall.data.status == "closed"

    # Re-open after close
    stall.open()
    stall.refresh()
    assert stall.data.status == "open"


def test_place_stall_with_direction(game):
    """Place stalls facing different directions."""
    game.park.cheats.build_in_pause_mode()

    for d in (Direction.WEST, Direction.NORTH, Direction.EAST, Direction.SOUTH):
        stall = game.rides.place_stall(
            obj=RideObjects.stall.BALLOON_STALL,
            tile=Tile(20 + d.value * 3, 20),
            direction=d,
        )
        stall.open()
        stall.refresh()
        assert stall.data.status == "open"


def test_place_stall_at_surface_height(game):
    """Stall placed without explicit height lands at surface level."""
    game.park.cheats.build_in_pause_mode()

    tile = Tile(20, 20)
    surface_z = game.world.get_tile(tile).surface.baseZ

    game.rides.place_stall(
        obj=RideObjects.stall.INFORMATION_KIOSK,
        tile=tile,
    )

    track = game.world.get_tile(tile).tracks[0]
    assert track.baseZ == surface_z


def test_place_stall_rejects_non_stall(game):
    """Passing a non-stall object raises ValueError."""
    game.park.cheats.build_in_pause_mode()

    with pytest.raises(ValueError, match="not a stall"):
        game.rides.place_stall(
            obj=RideObjects.gentle.MERRY_GO_ROUND,
            tile=Tile(20, 20),
        )


def test_place_stall_height_too_low(game):
    """Placing a stall below the surface raises ValueError."""
    game.park.cheats.build_in_pause_mode()

    with pytest.raises(ValueError, match="below the surface"):
        game.rides.place_stall(
            obj=RideObjects.stall.BURGER_BAR,
            tile=Tile(20, 20),
            height=1,
        )


def test_place_stall_in_the_sky(game):
    """Stall placed with explicit height floats above the surface."""
    game.park.cheats.build_in_pause_mode()

    from pyrct2.world._slope import LAND_HEIGHT_STEP

    tile = Tile(20, 20)
    surface_steps = game.world.get_tile(tile).surface.baseZ // LAND_HEIGHT_STEP

    target_height = surface_steps + 5
    game.rides.place_stall(
        obj=RideObjects.stall.BURGER_BAR,
        tile=tile,
        height=target_height,
    )

    track = game.world.get_tile(tile).tracks[0]
    assert track.baseZ == target_height * LAND_HEIGHT_STEP


def test_place_stall_on_occupied_tile(game):
    """Placing a stall on an occupied tile without explicit height raises ActionError."""
    from pyrct2.errors import ActionError

    game.park.cheats.build_in_pause_mode()

    tile = Tile(20, 20)
    game.rides.place_stall(obj=RideObjects.stall.BURGER_BAR, tile=tile)

    with pytest.raises(ActionError):
        game.rides.place_stall(obj=RideObjects.stall.BURGER_BAR, tile=tile)


def test_place_stall_stacked_above_existing(game):
    """Placing a stall above an existing one with explicit height succeeds."""
    from pyrct2.world._slope import LAND_HEIGHT_STEP

    game.park.cheats.build_in_pause_mode()

    tile = Tile(20, 20)
    game.rides.place_stall(obj=RideObjects.stall.BURGER_BAR, tile=tile)

    surface_steps = game.world.get_tile(tile).surface.baseZ // LAND_HEIGHT_STEP
    game.rides.place_stall(
        obj=RideObjects.stall.BURGER_BAR,
        tile=tile,
        height=surface_steps + 5,
    )
