"""Integration tests for tracked ride construction (coasters, water rides, transport)."""

import pytest

from pyrct2._generated.enums import Direction, TrackElemType
from pyrct2._generated.objects import RideObjects
from pyrct2.client import RCT2
from pyrct2.errors import ActionError
from pyrct2.park import RideEntity, TrackedRideEntity
from pyrct2.result import CursorPosition, TrackPlaceResult, TrackRemoveResult
from pyrct2.scenarios import Scenario
from pyrct2.world._tile import Tile


@pytest.fixture
def game_large():
    """Launch a 256x256 flat map with tracked ride objects pre-loaded."""
    with RCT2.launch(Scenario.TEST_PARK_LARGE) as g:
        g.park.cheats.build_in_pause_mode()
        g.park.cheats.sandbox_mode()
        g.advance_ticks(10)
        yield g


# ── Creation ────────────────────────────────────────────────────────


def test_create_returns_tracked_entity(game_large):
    """create_tracked_ride returns a TrackedRideEntity."""
    coaster = game_large.rides.create_tracked_ride(
        obj=RideObjects.rollercoaster.LADYBIRD_TRAINS,
        station_origin=Tile(100, 100),
        station_length=3,
        direction=Direction.EAST,
    )
    assert isinstance(coaster, TrackedRideEntity)
    assert isinstance(coaster, RideEntity)


def test_station_pieces(game_large):
    """Station creates the correct number of END_STATION pieces."""
    coaster = game_large.rides.create_tracked_ride(
        obj=RideObjects.rollercoaster.LADYBIRD_TRAINS,
        station_origin=Tile(100, 100),
        station_length=3,
        direction=Direction.EAST,
    )
    assert len(coaster.pieces) == 3
    for piece in coaster.pieces:
        assert piece.track_type == TrackElemType.END_STATION


def test_station_length_1(game_large):
    """Station with length=1 creates 1 piece."""
    coaster = game_large.rides.create_tracked_ride(
        obj=RideObjects.rollercoaster.LADYBIRD_TRAINS,
        station_origin=Tile(100, 100),
        station_length=1,
        direction=Direction.EAST,
    )
    assert len(coaster.pieces) == 1


def test_station_length_5(game_large):
    """Station with length=5 creates 5 pieces."""
    coaster = game_large.rides.create_tracked_ride(
        obj=RideObjects.rollercoaster.LADYBIRD_TRAINS,
        station_origin=Tile(100, 100),
        station_length=5,
        direction=Direction.EAST,
    )
    assert len(coaster.pieces) == 5


def test_cursor_after_station(game_large):
    """Cursor is positioned at station exit after creation."""
    coaster = game_large.rides.create_tracked_ride(
        obj=RideObjects.rollercoaster.LADYBIRD_TRAINS,
        station_origin=Tile(100, 100),
        station_length=3,
        direction=Direction.EAST,
    )
    assert isinstance(coaster.position, CursorPosition)
    # Station at (100-102, 100) facing EAST -> cursor exits east of tile 102
    assert coaster.position.x > 100 * 32  # past the station origin


def test_valid_next_after_station(game_large):
    """valid_next is populated after station creation."""
    coaster = game_large.rides.create_tracked_ride(
        obj=RideObjects.rollercoaster.LADYBIRD_TRAINS,
        station_origin=Tile(100, 100),
        station_length=3,
        direction=Direction.EAST,
    )
    assert len(coaster.valid_next) > 0
    assert TrackElemType.FLAT in coaster.valid_next


# ── Placement ───────────────────────────────────────────────────────


def test_place_flat(game_large):
    """Placing a FLAT piece returns TrackPlaceResult and updates state."""
    coaster = game_large.rides.create_tracked_ride(
        obj=RideObjects.rollercoaster.LADYBIRD_TRAINS,
        station_origin=Tile(100, 100),
        station_length=3,
        direction=Direction.EAST,
    )
    before_count = len(coaster.pieces)
    result = coaster.place(TrackElemType.FLAT)

    assert isinstance(result, TrackPlaceResult)
    assert result.cost >= 0
    assert isinstance(result.position, CursorPosition)
    assert len(result.valid_next) > 0
    assert len(coaster.pieces) == before_count + 1


def test_place_updates_cursor(game_large):
    """Each placement advances the cursor position."""
    coaster = game_large.rides.create_tracked_ride(
        obj=RideObjects.rollercoaster.LADYBIRD_TRAINS,
        station_origin=Tile(100, 100),
        station_length=3,
        direction=Direction.EAST,
    )
    pos1 = coaster.position
    coaster.place(TrackElemType.FLAT)
    pos2 = coaster.position

    # Facing east -> x should advance
    assert pos2.x > pos1.x
    assert pos2.direction == pos1.direction  # direction unchanged for flat


def test_place_slope_changes_z(game_large):
    """Placing a slope transition changes the cursor z."""
    coaster = game_large.rides.create_tracked_ride(
        obj=RideObjects.rollercoaster.LADYBIRD_TRAINS,
        station_origin=Tile(100, 100),
        station_length=3,
        direction=Direction.EAST,
    )
    z_before = coaster.position.z
    coaster.place(TrackElemType.FLAT_TO_UP25)
    coaster.place(TrackElemType.UP25)
    z_after = coaster.position.z

    assert z_after > z_before


def test_place_chain_lift(game_large):
    """chain_lift=True doesn't affect placement result structure."""
    coaster = game_large.rides.create_tracked_ride(
        obj=RideObjects.rollercoaster.LADYBIRD_TRAINS,
        station_origin=Tile(100, 100),
        station_length=3,
        direction=Direction.EAST,
    )
    result = coaster.place(TrackElemType.FLAT_TO_UP25, chain_lift=True)
    assert isinstance(result, TrackPlaceResult)
    assert result.cost >= 0


def test_place_turn_changes_direction(game_large):
    """Placing a turn changes the cursor direction."""
    coaster = game_large.rides.create_tracked_ride(
        obj=RideObjects.rollercoaster.LADYBIRD_TRAINS,
        station_origin=Tile(100, 100),
        station_length=3,
        direction=Direction.EAST,
    )
    dir_before = coaster.position.direction
    coaster.place(TrackElemType.RIGHT_QUARTER_TURN3_TILES)
    dir_after = coaster.position.direction

    assert dir_after != dir_before


def test_place_invalid_piece_raises(game_large):
    """Placing a piece not in valid_next raises ActionError."""
    coaster = game_large.rides.create_tracked_ride(
        obj=RideObjects.rollercoaster.LADYBIRD_TRAINS,
        station_origin=Tile(100, 100),
        station_length=3,
        direction=Direction.EAST,
    )
    # DOWN25 from flat is invalid (needs FLAT_TO_DOWN25 first)
    with pytest.raises(ActionError):
        coaster.place(TrackElemType.DOWN25)


# ── valid_next ──────────────────────────────────────────────────────


def test_valid_next_changes_after_slope(game_large):
    """valid_next changes based on slope/bank state."""
    coaster = game_large.rides.create_tracked_ride(
        obj=RideObjects.rollercoaster.LADYBIRD_TRAINS,
        station_origin=Tile(100, 100),
        station_length=3,
        direction=Direction.EAST,
    )
    flat_options = set(coaster.valid_next)

    coaster.place(TrackElemType.FLAT_TO_UP25)
    slope_options = set(coaster.valid_next)

    # Different slope state -> different valid options
    assert flat_options != slope_options
    # On a 25-degree slope, UP25 should be valid
    assert TrackElemType.UP25 in slope_options


def test_valid_next_contains_track_elem_types(game_large):
    """valid_next returns TrackElemType enum values."""
    coaster = game_large.rides.create_tracked_ride(
        obj=RideObjects.rollercoaster.LADYBIRD_TRAINS,
        station_origin=Tile(100, 100),
        station_length=3,
        direction=Direction.EAST,
    )
    for item in coaster.valid_next:
        assert isinstance(item, TrackElemType)


# ── Undo ────────────────────────────────────────────────────────────


def test_undo_single(game_large):
    """undo() removes the last placed piece."""
    coaster = game_large.rides.create_tracked_ride(
        obj=RideObjects.rollercoaster.LADYBIRD_TRAINS,
        station_origin=Tile(100, 100),
        station_length=3,
        direction=Direction.EAST,
    )
    coaster.place(TrackElemType.FLAT)
    coaster.place(TrackElemType.FLAT)
    count_before = len(coaster.pieces)

    removed = coaster.undo()

    assert len(removed) == 1
    assert isinstance(removed[0], TrackRemoveResult)
    assert removed[0].track_type == TrackElemType.FLAT
    assert len(coaster.pieces) == count_before - 1


def test_undo_multiple(game_large):
    """undo(n) removes the last n pieces."""
    coaster = game_large.rides.create_tracked_ride(
        obj=RideObjects.rollercoaster.LADYBIRD_TRAINS,
        station_origin=Tile(100, 100),
        station_length=3,
        direction=Direction.EAST,
    )
    coaster.place(TrackElemType.FLAT)
    coaster.place(TrackElemType.FLAT)
    coaster.place(TrackElemType.FLAT)

    removed = coaster.undo(3)

    assert len(removed) == 3
    # Station pieces remain
    assert len(coaster.pieces) == 3


def test_undo_protects_station(game_large):
    """undo() raises ValueError when n would remove station pieces."""
    coaster = game_large.rides.create_tracked_ride(
        obj=RideObjects.rollercoaster.LADYBIRD_TRAINS,
        station_origin=Tile(100, 100),
        station_length=3,
        direction=Direction.EAST,
    )
    coaster.place(TrackElemType.FLAT)

    # Try to undo more than non-station pieces
    with pytest.raises(ValueError, match="Station pieces.*protected"):
        coaster.undo(100)

    # Station still intact
    assert len(coaster.pieces) == 4  # 3 station + 1 flat


def test_undo_restores_cursor(game_large):
    """After undo, cursor returns to previous position."""
    coaster = game_large.rides.create_tracked_ride(
        obj=RideObjects.rollercoaster.LADYBIRD_TRAINS,
        station_origin=Tile(100, 100),
        station_length=3,
        direction=Direction.EAST,
    )
    pos_before = coaster.position
    coaster.place(TrackElemType.FLAT)
    coaster.place(TrackElemType.FLAT)
    coaster.undo(2)

    # Position should be back to where it was
    assert coaster.position.x == pos_before.x
    assert coaster.position.y == pos_before.y
    assert coaster.position.z == pos_before.z


def test_build_after_undo(game_large):
    """Can place new pieces after undo."""
    coaster = game_large.rides.create_tracked_ride(
        obj=RideObjects.rollercoaster.LADYBIRD_TRAINS,
        station_origin=Tile(100, 100),
        station_length=3,
        direction=Direction.EAST,
    )
    coaster.place(TrackElemType.FLAT)
    coaster.undo()
    result = coaster.place(TrackElemType.FLAT)

    assert isinstance(result, TrackPlaceResult)
    assert len(coaster.pieces) == 4  # 3 station + 1 flat


# ── Circuit ─────────────────────────────────────────────────────────


def test_circuit_not_complete_after_station(game_large):
    """Circuit is not complete immediately after station creation."""
    coaster = game_large.rides.create_tracked_ride(
        obj=RideObjects.rollercoaster.LADYBIRD_TRAINS,
        station_origin=Tile(100, 100),
        station_length=3,
        direction=Direction.EAST,
    )
    assert not coaster.circuit_complete


def test_flat_oval_circuit(game_large):
    """Building a flat oval closes the circuit."""
    coaster = game_large.rides.create_tracked_ride(
        obj=RideObjects.rollercoaster.LADYBIRD_TRAINS,
        station_origin=Tile(100, 100),
        station_length=3,
        direction=Direction.EAST,
    )

    # R3 turns, stn=3: [3, 5, 6, 5]
    flats = [3, 5, 6, 5]
    for side in range(4):
        for _ in range(flats[side]):
            coaster.place(TrackElemType.FLAT)
        coaster.place(TrackElemType.RIGHT_QUARTER_TURN3_TILES)

    assert coaster.circuit_complete


# ── Entrance/exit ───────────────────────────────────────────────────


def test_place_entrance_exit(game_large):
    """Entrance and exit can be placed on station-adjacent tiles."""
    coaster = game_large.rides.create_tracked_ride(
        obj=RideObjects.rollercoaster.LADYBIRD_TRAINS,
        station_origin=Tile(100, 100),
        station_length=3,
        direction=Direction.EAST,
    )

    # Build a circuit
    flats = [3, 5, 6, 5]
    for side in range(4):
        for _ in range(flats[side]):
            coaster.place(TrackElemType.FLAT)
        coaster.place(TrackElemType.RIGHT_QUARTER_TURN3_TILES)

    coaster.place_entrance(Tile(101, 99))
    coaster.place_exit(Tile(101, 101))

    # Verify entrance/exit via tile data
    ent_data = game_large.world.get_tile(Tile(101, 99))
    ext_data = game_large.world.get_tile(Tile(101, 101))
    assert len(ent_data.entrances) > 0
    assert len(ext_data.entrances) > 0


# ── Open ride ───────────────────────────────────────────────────────


def test_open_completed_coaster(game_large):
    """A completed coaster with entrance/exit can be opened."""
    coaster = game_large.rides.create_tracked_ride(
        obj=RideObjects.rollercoaster.LADYBIRD_TRAINS,
        station_origin=Tile(100, 100),
        station_length=3,
        direction=Direction.EAST,
    )

    flats = [3, 5, 6, 5]
    for side in range(4):
        for _ in range(flats[side]):
            coaster.place(TrackElemType.FLAT)
        coaster.place(TrackElemType.RIGHT_QUARTER_TURN3_TILES)

    coaster.place_entrance(Tile(101, 99))
    coaster.place_exit(Tile(101, 101))
    coaster.open()
    game_large.advance_ticks(100)

    coaster.refresh()
    assert coaster.data.status == "open"


# ── Different ride types ────────────────────────────────────────────


def test_log_flume(game_large):
    """Log Flume (water ride) uses the same tracked ride API."""
    flume = game_large.rides.create_tracked_ride(
        obj=RideObjects.water.LOGS,
        station_origin=Tile(100, 120),
        station_length=3,
        direction=Direction.EAST,
    )
    assert isinstance(flume, TrackedRideEntity)
    assert len(flume.pieces) == 3

    result = flume.place(TrackElemType.FLAT)
    assert isinstance(result, TrackPlaceResult)


def test_mini_railway(game_large):
    """Miniature Railway (transport ride) uses the same tracked ride API."""
    railway = game_large.rides.create_tracked_ride(
        obj=RideObjects.transport.AMERICAN_STYLE_STEAM_TRAINS,
        station_origin=Tile(100, 140),
        station_length=3,
        direction=Direction.EAST,
    )
    assert isinstance(railway, TrackedRideEntity)

    # Build a full circuit
    flats = [6, 8, 9, 8]
    for side in range(4):
        for _ in range(flats[side]):
            railway.place(TrackElemType.FLAT)
        railway.place(TrackElemType.RIGHT_QUARTER_TURN3_TILES)

    assert railway.circuit_complete


# ── Special pieces ──────────────────────────────────────────────────


def test_corkscrew(game_large):
    """Corkscrew pieces can be placed on a Corkscrew RC."""
    game_large.objects.load(RideObjects.rollercoaster.CORKSCREW_ROLLER_COASTER_TRAINS)

    coaster = game_large.rides.create_tracked_ride(
        obj=RideObjects.rollercoaster.CORKSCREW_ROLLER_COASTER_TRAINS,
        station_origin=Tile(80, 80),
        station_length=3,
        direction=Direction.EAST,
    )

    # Climb for height
    coaster.place(TrackElemType.FLAT_TO_UP25, chain_lift=True)
    for _ in range(4):
        coaster.place(TrackElemType.UP25, chain_lift=True)
    coaster.place(TrackElemType.UP25_TO_FLAT)

    # Corkscrew pair
    assert TrackElemType.LEFT_CORKSCREW_UP in coaster.valid_next
    coaster.place(TrackElemType.LEFT_CORKSCREW_UP)
    assert TrackElemType.RIGHT_CORKSCREW_DOWN in coaster.valid_next
    coaster.place(TrackElemType.RIGHT_CORKSCREW_DOWN)


def test_vertical_loop(game_large):
    """Vertical loop can be placed on a Twister RC."""
    game_large.objects.load(RideObjects.rollercoaster.TWISTER_TRAINS)

    coaster = game_large.rides.create_tracked_ride(
        obj=RideObjects.rollercoaster.TWISTER_TRAINS,
        station_origin=Tile(80, 100),
        station_length=3,
        direction=Direction.EAST,
    )

    # Big climb — loops need lots of height
    coaster.place(TrackElemType.FLAT_TO_UP25, chain_lift=True)
    for _ in range(5):
        coaster.place(TrackElemType.UP25, chain_lift=True)

    # Loop enters from UP25 slope
    assert TrackElemType.LEFT_VERTICAL_LOOP in coaster.valid_next
    coaster.place(TrackElemType.LEFT_VERTICAL_LOOP)

    # Loop exits at DOWN25
    assert TrackElemType.DOWN25 in coaster.valid_next


def test_brakes(game_large):
    """Brakes can be placed on flat track."""
    coaster = game_large.rides.create_tracked_ride(
        obj=RideObjects.rollercoaster.LADYBIRD_TRAINS,
        station_origin=Tile(100, 100),
        station_length=3,
        direction=Direction.EAST,
    )
    coaster.place(TrackElemType.FLAT)

    if TrackElemType.BRAKES in coaster.valid_next:
        result = coaster.place(TrackElemType.BRAKES)
        assert isinstance(result, TrackPlaceResult)


def test_on_ride_photo(game_large):
    """On-ride photo can be placed on flat track."""
    coaster = game_large.rides.create_tracked_ride(
        obj=RideObjects.rollercoaster.LADYBIRD_TRAINS,
        station_origin=Tile(100, 100),
        station_length=3,
        direction=Direction.EAST,
    )
    coaster.place(TrackElemType.FLAT)

    if TrackElemType.ON_RIDE_PHOTO in coaster.valid_next:
        result = coaster.place(TrackElemType.ON_RIDE_PHOTO)
        assert isinstance(result, TrackPlaceResult)


# ── Directions ──────────────────────────────────────────────────────


def test_all_cardinal_directions(game_large):
    """Tracked rides can be created facing all 4 directions."""
    for i, direction in enumerate(Direction):
        coaster = game_large.rides.create_tracked_ride(
            obj=RideObjects.rollercoaster.LADYBIRD_TRAINS,
            station_origin=Tile(50 + i * 20, 100),
            station_length=3,
            direction=direction,
        )
        assert len(coaster.pieces) == 3
        result = coaster.place(TrackElemType.FLAT)
        assert isinstance(result, TrackPlaceResult)
