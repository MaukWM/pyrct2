"""Undo — removing track pieces.

Demonstrates using coaster.undo() to remove the last placed pieces.
Undo protects the station — you can't undo past the first station piece.

Run with:
    cd pyrct2 && uv run python examples/11_undo.py
"""

from pyrct2._generated.enums import Direction, TrackElemType
from pyrct2._generated.objects import RideObjects
from pyrct2.client import RCT2
from pyrct2.scenarios import Scenario
from pyrct2.world._tile import Tile

with RCT2.launch(Scenario.TEST_PARK_LARGE) as game:
    game.park.cheats.build_in_pause_mode()
    game.park.cheats.sandbox_mode()
    game.advance_ticks(10)

    coaster = game.rides.create_tracked_ride(
        obj=RideObjects.rollercoaster.LADYBIRD_TRAINS,
        station_origin=Tile(100, 100),
        station_length=3,
        direction=Direction.EAST,
    )

    # Build some track
    coaster.place(TrackElemType.FLAT)
    coaster.place(TrackElemType.FLAT)
    coaster.place(TrackElemType.FLAT)
    coaster.place(TrackElemType.FLAT_TO_UP25, chain_lift=True)
    coaster.place(TrackElemType.UP25, chain_lift=True)
    print(f"After building: {len(coaster.pieces)} pieces")

    # Undo last piece
    removed = coaster.undo()
    print(f"Undo 1: removed {removed[0].track_type.name}, now {len(coaster.pieces)} pieces")

    # Undo multiple pieces at once
    removed = coaster.undo(3)
    print(f"Undo 3: removed {[r.track_type.name for r in removed]}, now {len(coaster.pieces)} pieces")

    # Trying to undo past station raises ValueError
    try:
        coaster.undo(100)
    except ValueError as e:
        print(f"Undo 100: blocked — {e}")

    # Can still build after undo
    coaster.place(TrackElemType.FLAT)
    coaster.place(TrackElemType.FLAT)
    print(f"After rebuilding: {len(coaster.pieces)} pieces")
    print(f"Position: {coaster.position}")
