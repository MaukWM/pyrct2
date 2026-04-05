"""Integration tests for ride placement and RideEntity queries."""

import pytest

from pyrct2._generated.enums import Direction
from pyrct2._generated.objects import RideObjects
from pyrct2.rides import RideEntity
from pyrct2.world import Tile
from pyrct2.world._slope import LAND_HEIGHT_STEP


# ── Helpers ──────────────────────────────────────────────────────────


def _get_ride_status(game, ride_id: int) -> str:
    """Get the status string of a ride by ID."""
    rides = game.state.rides()
    ride = next(r for r in rides if r.id == ride_id)
    return ride.status


# ── Entrance/exit validation ─────────────────────────────────────────


def test_place_flat_ride_entrance_on_footprint(game):
    """Entrance placed on a footprint tile raises ValueError."""
    game.park.cheats.build_in_pause_mode()

    with pytest.raises(ValueError, match="Entrance.*inside the ride footprint"):
        game.rides.place_flat_ride(
            obj=RideObjects.gentle.MERRY_GO_ROUND,
            tile=Tile(20, 20),
            entrance=Tile(20, 20),  # center of 3x3 = inside footprint
            exit=Tile(20, 18),
        )


def test_place_flat_ride_exit_on_footprint(game):
    """Exit placed on a footprint tile raises ValueError."""
    game.park.cheats.build_in_pause_mode()

    with pytest.raises(ValueError, match="Exit.*inside the ride footprint"):
        game.rides.place_flat_ride(
            obj=RideObjects.gentle.MERRY_GO_ROUND,
            tile=Tile(20, 20),
            entrance=Tile(20, 22),
            exit=Tile(21, 21),  # corner of 3x3 = inside footprint
        )


def test_place_flat_ride_entrance_not_adjacent(game):
    """Entrance far from footprint raises ValueError."""
    game.park.cheats.build_in_pause_mode()

    with pytest.raises(ValueError, match="Entrance.*not adjacent"):
        game.rides.place_flat_ride(
            obj=RideObjects.gentle.MERRY_GO_ROUND,
            tile=Tile(20, 20),
            entrance=Tile(20, 28),  # far away
            exit=Tile(20, 18),
        )


def test_place_flat_ride_exit_not_adjacent(game):
    """Exit far from footprint raises ValueError."""
    game.park.cheats.build_in_pause_mode()

    with pytest.raises(ValueError, match="Exit.*not adjacent"):
        game.rides.place_flat_ride(
            obj=RideObjects.gentle.MERRY_GO_ROUND,
            tile=Tile(20, 20),
            entrance=Tile(20, 22),
            exit=Tile(20, 10),  # far away
        )


def test_place_flat_ride_entrance_diagonal(game):
    """Entrance on a diagonal tile (not cardinally adjacent) raises ValueError."""
    game.park.cheats.build_in_pause_mode()

    # 3x3 centered at (20,20) → footprint (19,19)-(21,21)
    # (22,22) is diagonal to corner (21,21), not cardinally adjacent
    with pytest.raises(ValueError, match="Entrance.*not adjacent"):
        game.rides.place_flat_ride(
            obj=RideObjects.gentle.MERRY_GO_ROUND,
            tile=Tile(20, 20),
            entrance=Tile(22, 22),
            exit=Tile(20, 18),
        )


# ── Integration tests ────────────────────────────────────────────────


def test_place_flat_ride_open_close(game):
    """Place a Merry-Go-Round, verify placement, open/close with status checks."""
    game.park.cheats.build_in_pause_mode()

    ride_id = game.rides.place_flat_ride(
        obj=RideObjects.gentle.MERRY_GO_ROUND,
        tile=Tile(20, 20),
        entrance=Tile(20, 22),
        exit=Tile(20, 18),
    )

    # Verify track on the center tile
    tile_data = game.world.get_tile(Tile(20, 20))
    assert len(tile_data.tracks) > 0

    # Verify entrance and exit
    assert len(game.world.get_tile(Tile(20, 22)).entrances) > 0
    assert len(game.world.get_tile(Tile(20, 18)).entrances) > 0

    # Starts closed
    assert _get_ride_status(game, ride_id) == "closed"

    # Open
    game.rides.open(ride_id)
    assert _get_ride_status(game, ride_id) == "open"

    # Open again (idempotent)
    game.rides.open(ride_id)
    assert _get_ride_status(game, ride_id) == "open"

    # Close
    game.rides.close(ride_id)
    assert _get_ride_status(game, ride_id) == "closed"

    # Close again (idempotent)
    game.rides.close(ride_id)
    assert _get_ride_status(game, ride_id) == "closed"

    # Re-open after close
    game.rides.open(ride_id)
    assert _get_ride_status(game, ride_id) == "open"


def test_place_flat_ride_with_direction(game):
    """Place rides facing different directions."""
    game.park.cheats.build_in_pause_mode()

    for i, d in enumerate(Direction):
        x = 20 + i * 5
        ride_id = game.rides.place_flat_ride(
            obj=RideObjects.gentle.MERRY_GO_ROUND,
            tile=Tile(x, 20),
            entrance=Tile(x, 22),
            exit=Tile(x, 18),
            direction=d,
        )
        game.rides.open(ride_id)
        assert _get_ride_status(game, ride_id) == "open"


def test_place_flat_ride_height_too_low(game):
    """Placing a ride below the surface raises ValueError."""
    game.park.cheats.build_in_pause_mode()

    with pytest.raises(ValueError, match="below the surface"):
        game.rides.place_flat_ride(
            obj=RideObjects.gentle.MERRY_GO_ROUND,
            tile=Tile(20, 20),
            entrance=Tile(20, 22),
            exit=Tile(20, 18),
            height=1,
        )


def test_place_flat_ride_at_surface_height(game):
    """Ride placed without explicit height lands at surface level."""
    game.park.cheats.build_in_pause_mode()

    tile = Tile(20, 20)
    surface_z = game.world.get_tile(tile).surface.baseZ

    _ = game.rides.place_flat_ride(
        obj=RideObjects.gentle.MERRY_GO_ROUND,
        tile=tile,
        entrance=Tile(20, 22),
        exit=Tile(20, 18),
    )

    track = game.world.get_tile(tile).tracks[0]
    assert track.baseZ == surface_z


def test_place_flat_ride_on_raised_terrain(game):
    """Ride placed on raised terrain lands at the new height."""
    game.park.cheats.build_in_pause_mode()

    tile = Tile(30, 30)
    before_z = game.world.get_tile(tile).surface.baseZ

    game.world.raise_land(tile)
    after_z = game.world.get_tile(tile).surface.baseZ
    assert after_z > before_z

    _ = game.rides.place_flat_ride(
        obj=RideObjects.gentle.MERRY_GO_ROUND,
        tile=tile,
        entrance=Tile(30, 32),
        exit=Tile(30, 28),
    )

    track = game.world.get_tile(tile).tracks[0]
    assert track.baseZ == after_z


def test_place_flat_ride_in_the_sky(game):
    """Ride placed with explicit height floats above the surface."""
    game.park.cheats.build_in_pause_mode()

    tile = Tile(20, 20)
    surface_steps = game.world.get_tile(tile).surface.baseZ // LAND_HEIGHT_STEP

    target_height = surface_steps + 5
    _ = game.rides.place_flat_ride(
        obj=RideObjects.gentle.MERRY_GO_ROUND,
        tile=tile,
        entrance=Tile(20, 22),
        exit=Tile(20, 18),
        height=target_height,
    )

    track = game.world.get_tile(tile).tracks[0]
    assert track.baseZ == target_height * LAND_HEIGHT_STEP


def test_place_flat_ride_on_occupied_tile(game):
    """Placing a ride on an occupied tile without explicit height raises ActionError."""
    from pyrct2.errors import ActionError

    game.park.cheats.build_in_pause_mode()

    tile = Tile(20, 20)
    game.rides.place_flat_ride(
        obj=RideObjects.gentle.MERRY_GO_ROUND,
        tile=tile,
        entrance=Tile(20, 22),
        exit=Tile(20, 18),
    )

    with pytest.raises(ActionError):
        game.rides.place_flat_ride(
            obj=RideObjects.gentle.MERRY_GO_ROUND,
            tile=tile,
            entrance=Tile(22, 20),
            exit=Tile(18, 20),
        )


def test_place_flat_ride_stacked_above_existing(game):
    """Placing a ride above an existing one with explicit height succeeds."""
    game.park.cheats.build_in_pause_mode()

    tile = Tile(20, 20)
    game.rides.place_flat_ride(
        obj=RideObjects.gentle.MERRY_GO_ROUND,
        tile=tile,
        entrance=Tile(20, 22),
        exit=Tile(20, 18),
    )

    surface_steps = game.world.get_tile(tile).surface.baseZ // LAND_HEIGHT_STEP
    _ = game.rides.place_flat_ride(
        obj=RideObjects.gentle.MERRY_GO_ROUND,
        tile=tile,
        entrance=Tile(22, 20),
        exit=Tile(18, 20),
        height=surface_steps + 5,
    )


# ── RideEntity query tests ──────────────────────────────────────────


def test_list_empty(game):
    """Empty park has no rides."""
    assert game.rides.list() == []


def test_list_multiple(game):
    """Multiple placed rides all appear in list."""
    game.park.cheats.build_in_pause_mode()

    game.rides.place_flat_ride(
        obj=RideObjects.gentle.MERRY_GO_ROUND,
        tile=Tile(20, 20),
        entrance=Tile(20, 22),
        exit=Tile(20, 18),
    )
    game.rides.place_flat_ride(
        obj=RideObjects.gentle.MERRY_GO_ROUND,
        tile=Tile(30, 20),
        entrance=Tile(30, 22),
        exit=Tile(30, 18),
    )

    rides = game.rides.list()
    assert len(rides) == 2
    assert all(isinstance(r, RideEntity) for r in rides)
    assert rides[0].name == "Merry-Go-Round 1"
    assert rides[1].name == "Merry-Go-Round 2"
    assert rides[0].status == "closed"
    assert rides[1].status == "closed"


def test_get_multiple(game):
    """Get correct ride by ID when multiple exist."""
    game.park.cheats.build_in_pause_mode()

    id_1 = game.rides.place_flat_ride(
        obj=RideObjects.gentle.MERRY_GO_ROUND,
        tile=Tile(20, 20),
        entrance=Tile(20, 22),
        exit=Tile(20, 18),
    )
    id_2 = game.rides.place_flat_ride(
        obj=RideObjects.gentle.MERRY_GO_ROUND,
        tile=Tile(30, 20),
        entrance=Tile(30, 22),
        exit=Tile(30, 18),
    )

    ride_1 = game.rides.get(id_1)
    ride_2 = game.rides.get(id_2)
    assert ride_1 is not None
    assert ride_2 is not None
    assert ride_1._id == id_1
    assert ride_2._id == id_2
    assert ride_1.name == "Merry-Go-Round 1"
    assert ride_2.name == "Merry-Go-Round 2"


def test_get_nonexistent(game):
    """Get a ride that doesn't exist returns None."""
    assert game.rides.get(999) is None
