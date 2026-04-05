"""Integration tests for ride placement and RideEntity queries."""

import pytest

from pyrct2._generated.enums import Direction, RideInspection
from pyrct2._generated.objects import RideObjects
from pyrct2.rides import RideEntity, StationAccess
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
    assert rides[0].data.name == "Merry-Go-Round 1"
    assert rides[1].data.name == "Merry-Go-Round 2"
    assert rides[0].data.status == "closed"
    assert rides[1].data.status == "closed"


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
    assert ride_1.data.name == "Merry-Go-Round 1"
    assert ride_2.data.name == "Merry-Go-Round 2"


def test_get_nonexistent(game):
    """Get a ride that doesn't exist returns None."""
    assert game.rides.get(999) is None


# ── RideEntity property tests ───────────────────────────────────────


def test_ride_entity_properties(game):
    """Ride entity returns correct placement_tile, entrance, exit, and direction=None."""
    game.park.cheats.build_in_pause_mode()

    ride_id = game.rides.place_flat_ride(
        obj=RideObjects.gentle.MERRY_GO_ROUND,
        tile=Tile(20, 20),
        entrance=Tile(20, 22),
        exit=Tile(20, 18),
        direction=Direction.EAST,
    )

    ride = game.rides.get(ride_id)

    # Placement tile matches what was passed to place_flat_ride
    assert ride.placement_tile == Tile(20, 20)

    # Rides don't have a meaningful direction
    assert ride.direction is None

    # Entrance
    assert isinstance(ride.entrance, StationAccess)
    assert ride.entrance.tile == Tile(20, 22)
    assert ride.entrance.direction == Direction.EAST

    # Exit
    assert isinstance(ride.exit, StationAccess)
    assert ride.exit.tile == Tile(20, 18)
    assert ride.exit.direction == Direction.EAST


def test_stall_entity_properties(game):
    """Stall entity returns correct placement_tile, direction, and entrance/exit=None."""
    game.park.cheats.build_in_pause_mode()

    stall_id = game.rides.place_stall(
        obj=RideObjects.stall.BURGER_BAR,
        tile=Tile(25, 25),
        direction=Direction.SOUTH,
    )

    stall = game.rides.get(stall_id)

    # Placement tile matches
    assert stall.placement_tile == Tile(25, 25)

    # Stalls have a facing direction
    assert stall.direction == Direction.SOUTH

    # Stalls have no entrance/exit
    assert stall.entrance is None
    assert stall.exit is None


# ── RideEntity write method tests ────────────────────────────────────


def test_ride_entity_open_close(game):
    """Open and close a ride via entity methods."""
    game.park.cheats.build_in_pause_mode()

    ride_id = game.rides.place_flat_ride(
        obj=RideObjects.gentle.MERRY_GO_ROUND,
        tile=Tile(20, 20),
        entrance=Tile(20, 22),
        exit=Tile(20, 18),
    )

    ride = game.rides.get(ride_id)
    assert ride.data.status == "closed"

    ride.open()
    assert game.rides.get(ride_id).data.status == "open"

    ride.close()
    assert game.rides.get(ride_id).data.status == "closed"


def test_ride_entity_set_price(game):
    """Set ride entry price via entity."""
    game.park.cheats.build_in_pause_mode()

    ride_id = game.rides.place_flat_ride(
        obj=RideObjects.gentle.MERRY_GO_ROUND,
        tile=Tile(20, 20),
        entrance=Tile(20, 22),
        exit=Tile(20, 18),
    )

    ride = game.rides.get(ride_id)
    ride.set_price(50)
    assert game.rides.get(ride_id).data.price[0] == 50


def test_stall_entity_set_price(game):
    """Set stall price via entity."""
    game.park.cheats.build_in_pause_mode()

    stall_id = game.rides.place_stall(
        obj=RideObjects.stall.BURGER_BAR,
        tile=Tile(20, 20),
    )

    stall = game.rides.get(stall_id)
    stall.set_price(30)
    assert game.rides.get(stall_id).data.price[0] == 30


def test_ride_entity_demolish(game):
    """Demolish a ride via entity, verify it's gone."""
    game.park.cheats.build_in_pause_mode()

    ride_id = game.rides.place_flat_ride(
        obj=RideObjects.gentle.MERRY_GO_ROUND,
        tile=Tile(20, 20),
        entrance=Tile(20, 22),
        exit=Tile(20, 18),
    )

    ride = game.rides.get(ride_id)
    ride.demolish()
    assert game.rides.get(ride_id) is None
    assert game.rides.list() == []

    # Place again on the same tile, verify it works
    ride_id_2 = game.rides.place_flat_ride(
        obj=RideObjects.gentle.MERRY_GO_ROUND,
        tile=Tile(20, 20),
        entrance=Tile(20, 22),
        exit=Tile(20, 18),
    )
    ride_2 = game.rides.get(ride_id_2)
    assert ride_2 is not None
    assert len(game.rides.list()) == 1

    ride_2.demolish()
    assert game.rides.list() == []


def test_ride_entity_refresh(game):
    """Entity data is stale after write, refresh() updates it."""
    game.park.cheats.build_in_pause_mode()

    ride_id = game.rides.place_flat_ride(
        obj=RideObjects.gentle.MERRY_GO_ROUND,
        tile=Tile(20, 20),
        entrance=Tile(20, 22),
        exit=Tile(20, 18),
    )

    ride = game.rides.get(ride_id)
    old_price = ride.data.price[0]

    ride.set_price(77)

    # Data is stale — still shows old price
    assert ride.data.price[0] == old_price

    ride.refresh()

    # Now it's updated
    assert ride.data.price[0] == 77


def test_ride_entity_set_wait_times(game):
    """Set min and max wait times via entity."""
    game.park.cheats.build_in_pause_mode()

    ride_id = game.rides.place_flat_ride(
        obj=RideObjects.gentle.MERRY_GO_ROUND,
        tile=Tile(20, 20),
        entrance=Tile(20, 22),
        exit=Tile(20, 18),
    )

    ride = game.rides.get(ride_id)
    ride.set_min_wait_time(30)
    ride.set_max_wait_time(90)

    updated = game.rides.get(ride_id)
    assert updated.data.minimumWaitingTime == 30
    assert updated.data.maximumWaitingTime == 90


def test_ride_entity_set_inspection_interval(game):
    """Set inspection interval via entity."""
    game.park.cheats.build_in_pause_mode()

    ride_id = game.rides.place_flat_ride(
        obj=RideObjects.gentle.MERRY_GO_ROUND,
        tile=Tile(20, 20),
        entrance=Tile(20, 22),
        exit=Tile(20, 18),
    )

    ride = game.rides.get(ride_id)
    ride.set_inspection_interval(RideInspection.EVERY10_MINUTES)

    updated = game.rides.get(ride_id)
    assert updated.data.inspectionInterval == RideInspection.EVERY10_MINUTES
