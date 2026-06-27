"""Vertical loop coaster — a classic loop-the-loop.

Creates a Twister RC with a tall chain lift and a vertical loop.
The loop enters from a UP25 slope and exits at DOWN25.
This is an open layout for demonstration.

Run with:
    cd pyrct2 && uv run python examples/06_vertical_loop.py
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
    game.objects.load(RideObjects.rollercoaster.TWISTER_TRAINS)

    coaster = game.rides.create_tracked_ride(
        obj=RideObjects.rollercoaster.TWISTER_TRAINS,
        station_origin=Tile(100, 100),
        station_length=3,
        direction=Direction.EAST,
    )

    # Big chain lift — loops need lots of height
    coaster.place(TrackElemType.FLAT_TO_UP25, chain_lift=True)
    for _ in range(5):
        coaster.place(TrackElemType.UP25, chain_lift=True)

    # The loop! Enters from UP25 slope, exits at DOWN25 slope.
    coaster.place(TrackElemType.LEFT_VERTICAL_LOOP)
    print(f"Loop placed! z={coaster.position.z}")

    # Descent from the loop's DOWN25 exit
    for _ in range(4):
        coaster.place(TrackElemType.DOWN25)
    coaster.place(TrackElemType.DOWN25_TO_FLAT)
    coaster.place(TrackElemType.BRAKES)
    for _ in range(3):
        coaster.place(TrackElemType.FLAT)

    print(f"Pieces: {len(coaster.pieces)} (open layout with loop)")
    print(f"Final position: {coaster.position}")
