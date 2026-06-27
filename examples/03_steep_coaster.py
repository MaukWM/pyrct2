"""Steep drop coaster — 60-degree slopes with brakes.

Creates a Twister RC with a steep chain lift climb (25->60 degree transition)
and a matching steep descent with brakes. Demonstrates steep slope transitions.

Run with:
    cd pyrct2 && uv run python examples/03_steep_coaster.py
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

    # L3 turns, stn=3: [n-2, m, n+1, m]

    # Side 0 (4 pieces): steep chain lift
    # FLAT -> 25deg -> 60deg -> 25deg -> FLAT
    coaster.place(TrackElemType.FLAT_TO_UP25, chain_lift=True)
    coaster.place(TrackElemType.UP25_TO_UP60)
    coaster.place(TrackElemType.UP60_TO_UP25)
    coaster.place(TrackElemType.UP25_TO_FLAT)
    coaster.place(TrackElemType.LEFT_QUARTER_TURN3_TILES)

    # Side 1 (5 pieces): flat at height
    for _ in range(5):
        coaster.place(TrackElemType.FLAT)
    coaster.place(TrackElemType.LEFT_QUARTER_TURN3_TILES)

    # Side 2 (7 pieces): steep descent + brakes
    coaster.place(TrackElemType.FLAT_TO_DOWN25)
    coaster.place(TrackElemType.DOWN25_TO_DOWN60)
    coaster.place(TrackElemType.DOWN60_TO_DOWN25)
    coaster.place(TrackElemType.DOWN25_TO_FLAT)
    coaster.place(TrackElemType.BRAKES)
    coaster.place(TrackElemType.FLAT)
    coaster.place(TrackElemType.FLAT)
    coaster.place(TrackElemType.LEFT_QUARTER_TURN3_TILES)

    # Side 3 (5 pieces): flat back
    for _ in range(5):
        coaster.place(TrackElemType.FLAT)
    coaster.place(TrackElemType.LEFT_QUARTER_TURN3_TILES)

    print(f"Pieces: {len(coaster.pieces)}, Circuit: {coaster.circuit_complete}")

    coaster.place_entrance(Tile(101, 99))
    coaster.place_exit(Tile(101, 101))
    coaster.open()
    game.advance_ticks(500)
    print(f"Status: {coaster.data.status}")
