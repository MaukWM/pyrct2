"""Integration tests for ride placement and RideEntity queries."""

import pytest

from pyrct2._generated.enums import Direction, RideInspection
from pyrct2._generated.objects import RideObjects
from pyrct2.errors import ActionError
from pyrct2.park import RideEntity, StationAccess
from pyrct2.world import Tile
from pyrct2.world._slope import LAND_HEIGHT_STEP


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


# ── Pre-check: entrance/exit tile clearance ─────────────────────────


def test_place_flat_ride_entrance_blocked_by_path(game):
    """Entrance on a tile with a footpath raises ValueError."""
    game.park.cheats.build_in_pause_mode()
    game.paths.place(Tile(20, 22))

    with pytest.raises(ValueError, match="blocked by"):
        game.rides.place_flat_ride(
            obj=RideObjects.gentle.MERRY_GO_ROUND,
            tile=Tile(20, 20),
            entrance=Tile(20, 22),
            exit=Tile(20, 18),
        )

    # No orphaned ride left behind
    assert game.rides.list() == []


def test_place_flat_ride_exit_blocked_by_path(game):
    """Exit on a tile with a footpath raises ValueError."""
    game.park.cheats.build_in_pause_mode()
    game.paths.place(Tile(20, 18))

    with pytest.raises(ValueError, match="blocked by"):
        game.rides.place_flat_ride(
            obj=RideObjects.gentle.MERRY_GO_ROUND,
            tile=Tile(20, 20),
            entrance=Tile(20, 22),
            exit=Tile(20, 18),
        )

    assert game.rides.list() == []


def test_place_flat_ride_entrance_blocked_by_existing_ride(game):
    """Entrance/exit on a tile with existing elements raises ValueError."""
    game.park.cheats.build_in_pause_mode()

    # First ride at (20, 20): footprint (19-21, 19-21)
    game.rides.place_flat_ride(
        obj=RideObjects.gentle.MERRY_GO_ROUND,
        tile=Tile(20, 20),
        entrance=Tile(22, 20),
        exit=Tile(18, 20),
    )

    # Second ride at (23, 20), directly adjacent: footprint (22-24, 19-21)
    # Entrance at (21, 20) has first ride's track → blocked
    with pytest.raises(ValueError, match="blocked by"):
        game.rides.place_flat_ride(
            obj=RideObjects.gentle.MERRY_GO_ROUND,
            tile=Tile(23, 20),
            entrance=Tile(21, 20),
            exit=Tile(25, 20),
        )

    assert len(game.rides.list()) == 1


# ── Local path check (_has_path_at) ──────────────────────────────────


def test_has_path_at(game):
    """Focused test for _has_path_at edge cases."""
    game.park.cheats.build_in_pause_mode()
    ride = game.rides.place_flat_ride(
        obj=RideObjects.gentle.MERRY_GO_ROUND,
        tile=Tile(20, 20),
        entrance=Tile(20, 22),
        exit=Tile(20, 18),
    )
    ent_tile, ent_edge = ride._ride_path_info(ride.entrance)
    ext_tile, _ = ride._ride_path_info(ride.exit)

    # No paths placed → False
    assert not ride._has_path_at(ent_tile, required_edge=ent_edge)
    assert not ride._has_path_at(ext_tile)

    # Place paths → entrance needs correct edge, exit accepts any path
    game.paths.place(Tile(20, 23), queue=True)
    game.paths.place(Tile(20, 17))
    assert ride._has_path_at(ent_tile, required_edge=ent_edge)
    assert ride._has_path_at(ext_tile)

    # Perpendicular queue: path exists but edge doesn't face entrance
    game.rides.get(ride.data.id).demolish()
    game.paths.place(Tile(19, 23))  # west — fences the queue E+W only
    game.paths.place(Tile(21, 23))  # east
    ride2 = game.rides.place_flat_ride(
        obj=RideObjects.gentle.MERRY_GO_ROUND,
        tile=Tile(20, 20),
        entrance=Tile(20, 22),
        exit=Tile(18, 20),
    )
    ent_tile2, ent_edge2 = ride2._ride_path_info(ride2.entrance)
    assert not ride2._has_path_at(ent_tile2, required_edge=ent_edge2)


# ── Reachability ─────────────────────────────────────────────────────
# Park entrance arrival tile is at (48, 30) in the test scenario.


def test_ride_not_reachable_without_paths(game):
    """Ride with no adjacent paths is not reachable."""
    game.park.cheats.build_in_pause_mode()
    ride = game.rides.place_flat_ride(
        obj=RideObjects.gentle.MERRY_GO_ROUND,
        tile=Tile(20, 20),
        entrance=Tile(20, 22),
        exit=Tile(20, 18),
    )
    assert not ride.is_entrance_reachable()
    assert not ride.is_exit_reachable()


def test_ride_not_reachable_without_connection_to_park(game):
    """Ride with adjacent paths but no connection to park entrance."""
    game.park.cheats.build_in_pause_mode()
    ride = game.rides.place_flat_ride(
        obj=RideObjects.gentle.MERRY_GO_ROUND,
        tile=Tile(20, 20),
        entrance=Tile(20, 22),
        exit=Tile(20, 18),
    )
    game.paths.place(Tile(20, 23), queue=True)
    game.paths.place(Tile(20, 17))
    assert not ride.is_entrance_reachable()
    assert not ride.is_exit_reachable()


def test_entrance_not_reachable_queue_perpendicular(game):
    """Queue perpendicular to entrance has no edge facing it.

    Queue between two E-W paths gets fenced on N/S. Ride entrance to
    the north can't connect because the queue has no north edge.
    """
    game.park.cheats.build_in_pause_mode()

    game.paths.place(Tile(19, 23))  # west path
    game.paths.place(Tile(20, 23), queue=True)  # queue
    game.paths.place(Tile(21, 23))  # east path

    ride = game.rides.place_flat_ride(
        obj=RideObjects.gentle.MERRY_GO_ROUND,
        tile=Tile(20, 20),
        entrance=Tile(20, 22),
        exit=Tile(18, 20),
    )
    assert not ride.is_entrance_reachable()

    # Exit just needs any adjacent path (no edge required)
    game.paths.place(Tile(17, 20))
    assert not ride.is_exit_reachable()  # path exists but not connected to park


def test_ride_reachable_from_park_entrance(game):
    """Ride with paths connected to the park entrance is reachable."""
    game.park.cheats.build_in_pause_mode()
    ride = game.rides.place_flat_ride(
        obj=RideObjects.gentle.MERRY_GO_ROUND,
        tile=Tile(20, 20),
        entrance=Tile(20, 22),
        exit=Tile(20, 18),
    )

    # Connect entrance → park entrance
    game.paths.place(Tile(20, 23), queue=True)
    game.paths.place_line(Tile(20, 24), Tile(20, 30))
    game.paths.place_line(Tile(20, 30), Tile(48, 30))
    assert ride.is_entrance_reachable()
    assert not ride.is_exit_reachable()

    # Connect exit → park entrance
    game.paths.place(Tile(20, 17))
    game.paths.place_line(Tile(20, 16), Tile(20, 17))
    game.paths.place_line(Tile(18, 17), Tile(20, 17))
    game.paths.place_line(Tile(18, 17), Tile(18, 30))
    game.paths.place_line(Tile(18, 30), Tile(48, 30))
    assert ride.is_exit_reachable()


def test_stall_not_reachable_without_path(game):
    """Stall without a facing path is not reachable."""
    game.park.cheats.build_in_pause_mode()
    stall = game.rides.place_stall(
        RideObjects.stall.BURGER_BAR,
        Tile(20, 20),
        direction=Direction.SOUTH,
    )
    assert not stall.is_stall_reachable()


def test_stall_facing_wrong_way(game):
    """Stall facing away from path is not reachable."""
    game.park.cheats.build_in_pause_mode()
    game.paths.place(Tile(20, 21))

    stall = game.rides.place_stall(
        RideObjects.stall.BURGER_BAR,
        Tile(20, 20),
        direction=Direction.NORTH,
    )
    assert not stall.is_stall_reachable()


# ── Integration tests ────────────────────────────────────────────────


def test_place_flat_ride_open_close(game):
    """Place a Merry-Go-Round, verify placement, open/close with status checks."""
    game.park.cheats.build_in_pause_mode()

    ride = game.rides.place_flat_ride(
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
    assert ride.data.status == "closed"

    # Open
    ride.open()
    ride.refresh()
    assert ride.data.status == "open"

    # Close
    ride.close()
    ride.refresh()
    assert ride.data.status == "closed"

    # Re-open after close
    ride.open()
    ride.refresh()
    assert ride.data.status == "open"


def test_place_flat_ride_with_direction(game):
    """Place rides facing different directions."""
    game.park.cheats.build_in_pause_mode()

    for i, d in enumerate(Direction):
        x = 20 + i * 5
        ride = game.rides.place_flat_ride(
            obj=RideObjects.gentle.MERRY_GO_ROUND,
            tile=Tile(x, 20),
            entrance=Tile(x, 22),
            exit=Tile(x, 18),
            direction=d,
        )
        ride.open()
        ride.refresh()
        assert ride.data.status == "open"


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

    game.rides.place_flat_ride(
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

    game.rides.place_flat_ride(
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
    game.rides.place_flat_ride(
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
    game.rides.place_flat_ride(
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

    ride_1 = game.rides.place_flat_ride(
        obj=RideObjects.gentle.MERRY_GO_ROUND,
        tile=Tile(20, 20),
        entrance=Tile(20, 22),
        exit=Tile(20, 18),
    )
    ride_2 = game.rides.place_flat_ride(
        obj=RideObjects.gentle.MERRY_GO_ROUND,
        tile=Tile(30, 20),
        entrance=Tile(30, 22),
        exit=Tile(30, 18),
    )

    assert ride_1.data.name == "Merry-Go-Round 1"
    assert ride_2.data.name == "Merry-Go-Round 2"
    assert ride_1._id != ride_2._id


def test_get_nonexistent(game):
    """Get a ride that doesn't exist returns None."""
    assert game.rides.get(999) is None


# ── RideEntity property tests ───────────────────────────────────────


def test_ride_entity_properties(game):
    """Ride entity returns correct placement_tile, entrance, exit, and direction=None."""
    game.park.cheats.build_in_pause_mode()

    ride = game.rides.place_flat_ride(
        obj=RideObjects.gentle.MERRY_GO_ROUND,
        tile=Tile(20, 20),
        entrance=Tile(20, 22),
        exit=Tile(20, 18),
        direction=Direction.EAST,
    )

    # Placement tile matches what was passed to place_flat_ride
    assert ride.placement_tile == Tile(20, 20)

    # Rides don't have a meaningful direction
    assert ride.direction is None

    # Entrance
    assert isinstance(ride.entrance, StationAccess)
    assert ride.entrance.tile == Tile(20, 22)
    assert ride.entrance.direction == Direction.SOUTH  # faces outward (south, away from ride)

    # Exit
    assert isinstance(ride.exit, StationAccess)
    assert ride.exit.tile == Tile(20, 18)
    assert ride.exit.direction == Direction.NORTH  # faces outward (north, away from ride)


def test_stall_entity_properties(game):
    """Stall entity returns correct placement_tile, direction, and entrance/exit=None."""
    game.park.cheats.build_in_pause_mode()

    stall = game.rides.place_stall(
        obj=RideObjects.stall.BURGER_BAR,
        tile=Tile(25, 25),
        direction=Direction.SOUTH,
    )

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

    ride = game.rides.place_flat_ride(
        obj=RideObjects.gentle.MERRY_GO_ROUND,
        tile=Tile(20, 20),
        entrance=Tile(20, 22),
        exit=Tile(20, 18),
    )
    assert ride.data.status == "closed"

    ride.open()
    ride.refresh()
    assert ride.data.status == "open"

    ride.close()
    ride.refresh()
    assert ride.data.status == "closed"


def test_ride_entity_rename(game):
    """Rename a ride via entity."""
    game.park.cheats.build_in_pause_mode()

    ride = game.rides.place_flat_ride(
        obj=RideObjects.gentle.MERRY_GO_ROUND,
        tile=Tile(20, 20),
        entrance=Tile(20, 22),
        exit=Tile(20, 18),
    )
    assert ride.data.name == "Merry-Go-Round 1"

    ride.rename("x")
    ride.refresh()
    assert ride.data.name == "x"


def test_stall_entity_rename(game):
    """Rename a stall via entity."""
    game.park.cheats.build_in_pause_mode()

    stall = game.rides.place_stall(RideObjects.stall.BURGER_BAR, Tile(20, 20))
    stall.rename("y")
    stall.refresh()
    assert stall.data.name == "y"


def test_ride_entity_set_price(game):
    """Set ride entry price via entity."""
    game.park.cheats.build_in_pause_mode()

    ride = game.rides.place_flat_ride(
        obj=RideObjects.gentle.MERRY_GO_ROUND,
        tile=Tile(20, 20),
        entrance=Tile(20, 22),
        exit=Tile(20, 18),
    )

    ride.set_price(50)
    ride.refresh()
    assert ride.data.price[0] == 50


def test_stall_entity_set_price(game):
    """Set stall price via entity."""
    game.park.cheats.build_in_pause_mode()

    stall = game.rides.place_stall(
        obj=RideObjects.stall.BURGER_BAR,
        tile=Tile(20, 20),
    )

    stall.set_price(30)
    stall.refresh()
    assert stall.data.price[0] == 30


def test_ride_entity_demolish(game):
    """Demolish a ride via entity, verify it's gone."""
    game.park.cheats.build_in_pause_mode()

    ride = game.rides.place_flat_ride(
        obj=RideObjects.gentle.MERRY_GO_ROUND,
        tile=Tile(20, 20),
        entrance=Tile(20, 22),
        exit=Tile(20, 18),
    )

    ride.demolish()
    assert game.rides.get(ride.data.id) is None
    assert game.rides.list() == []

    # Place again on the same tile, verify it works
    ride_2 = game.rides.place_flat_ride(
        obj=RideObjects.gentle.MERRY_GO_ROUND,
        tile=Tile(20, 20),
        entrance=Tile(20, 22),
        exit=Tile(20, 18),
    )
    assert ride_2 is not None
    assert len(game.rides.list()) == 1

    ride_2.demolish()
    assert game.rides.list() == []


def test_ride_entity_refresh(game):
    """Entity data is stale after write, refresh() updates it."""
    game.park.cheats.build_in_pause_mode()

    ride = game.rides.place_flat_ride(
        obj=RideObjects.gentle.MERRY_GO_ROUND,
        tile=Tile(20, 20),
        entrance=Tile(20, 22),
        exit=Tile(20, 18),
    )

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

    ride = game.rides.place_flat_ride(
        obj=RideObjects.gentle.MERRY_GO_ROUND,
        tile=Tile(20, 20),
        entrance=Tile(20, 22),
        exit=Tile(20, 18),
    )

    ride.set_min_wait_time(30)
    ride.set_max_wait_time(90)

    ride.refresh()
    assert ride.data.minimumWaitingTime == 30
    assert ride.data.maximumWaitingTime == 90


def test_ride_entity_set_inspection_interval(game):
    """Set inspection interval via entity."""
    game.park.cheats.build_in_pause_mode()

    ride = game.rides.place_flat_ride(
        obj=RideObjects.gentle.MERRY_GO_ROUND,
        tile=Tile(20, 20),
        entrance=Tile(20, 22),
        exit=Tile(20, 18),
    )

    ride.set_inspection_interval(RideInspection.EVERY10_MINUTES)

    ride.refresh()
    assert ride.data.inspectionInterval == RideInspection.EVERY10_MINUTES
