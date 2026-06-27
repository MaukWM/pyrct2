"""Corkscrew coaster — double corkscrew with chain lift.

Creates a Corkscrew RC with a tall chain lift and two corkscrew pairs.
Corkscrews come in pairs: UP rotates the train, DOWN brings it back level.
This is an open layout (no circuit) for demonstration.

Run with:
    cd pyrct2 && uv run python examples/05_corkscrew_coaster.py
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

    # Tall chain lift — corkscrews need height
    coaster.place(TrackElemType.FLAT_TO_UP25, chain_lift=True)
    for _ in range(5):
        coaster.place(TrackElemType.UP25, chain_lift=True)
    coaster.place(TrackElemType.UP25_TO_FLAT)

    # Corkscrew pair 1: LEFT UP then RIGHT DOWN
    coaster.place(TrackElemType.LEFT_CORKSCREW_UP)
    coaster.place(TrackElemType.RIGHT_CORKSCREW_DOWN)
    print(f"Corkscrew 1 done! z={coaster.position.z}")

    # Flat section between corkscrews
    for _ in range(4):
        coaster.place(TrackElemType.FLAT)

    # Corkscrew pair 2: RIGHT UP then LEFT DOWN
    coaster.place(TrackElemType.RIGHT_CORKSCREW_UP)
    coaster.place(TrackElemType.LEFT_CORKSCREW_DOWN)
    print(f"Corkscrew 2 done! z={coaster.position.z}")

    # Descent back to ground
    for _ in range(2):
        coaster.place(TrackElemType.FLAT)
    coaster.place(TrackElemType.FLAT_TO_DOWN25)
    for _ in range(3):
        coaster.place(TrackElemType.DOWN25)
    coaster.place(TrackElemType.DOWN25_TO_FLAT)
    coaster.place(TrackElemType.BRAKES)
    for _ in range(3):
        coaster.place(TrackElemType.FLAT)

    print(f"Pieces: {len(coaster.pieces)} (open layout)")
    print(f"Final position: {coaster.position}")
