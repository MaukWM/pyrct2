"""Using valid_next — check what pieces can be placed.

Demonstrates using coaster.valid_next to inspect available track pieces
before placing them. This is how an LLM agent would decide what to build.

Run with:
    cd pyrct2 && uv run python examples/10_using_valid_next.py
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
    game.objects.load(RideObjects.rollercoaster.CORKSCREW_ROLLER_COASTER_TRAINS)

    coaster = game.rides.create_tracked_ride(
        obj=RideObjects.rollercoaster.CORKSCREW_ROLLER_COASTER_TRAINS,
        station_origin=Tile(100, 100),
        station_length=3,
        direction=Direction.EAST,
    )

    # After station placement, check what's available
    print("After station:")
    print(f"  Valid next: {[t.name for t in coaster.valid_next]}")
    print(f"  Cursor: {coaster.position}")

    # Build a climb
    coaster.place(TrackElemType.FLAT_TO_UP25, chain_lift=True)
    print("\nAfter FLAT_TO_UP25:")
    print(f"  Valid next: {[t.name for t in coaster.valid_next]}")

    for _ in range(3):
        coaster.place(TrackElemType.UP25, chain_lift=True)
    coaster.place(TrackElemType.UP25_TO_FLAT)

    # Check if corkscrew is available for this ride type
    print("\nAfter climb (flat at height):")
    print(f"  Valid next: {[t.name for t in coaster.valid_next]}")

    if TrackElemType.LEFT_CORKSCREW_UP in coaster.valid_next:
        print("  -> Corkscrew available! Placing it...")
        coaster.place(TrackElemType.LEFT_CORKSCREW_UP)

        # After corkscrew UP, the suggested next piece chains automatically
        print("\nAfter LEFT_CORKSCREW_UP:")
        print(f"  Valid next: {[t.name for t in coaster.valid_next]}")

        if TrackElemType.RIGHT_CORKSCREW_DOWN in coaster.valid_next:
            coaster.place(TrackElemType.RIGHT_CORKSCREW_DOWN)
            print("  -> Placed RIGHT_CORKSCREW_DOWN (chained suggestion)")
    else:
        print("  -> No corkscrew for this ride type")

    # Check if vertical loop is available
    if TrackElemType.LEFT_VERTICAL_LOOP in coaster.valid_next:
        print("  -> Vertical loop also available!")

    print(f"\nTotal pieces: {len(coaster.pieces)}")
    print(f"Position: {coaster.position}")
