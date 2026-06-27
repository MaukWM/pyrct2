"""Hill coaster — chain lift climb with descent.

Creates a Junior RC that climbs a hill with a chain lift and descends back
to station level. Demonstrates slope transitions and chain_lift parameter.

Run with:
    cd pyrct2 && uv run python examples/02_hill_coaster.py
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

    # R3 turns, stn=3, formula [n-2, m, n+1, m]. Using n=5, m=5 -> [3, 5, 6, 5]

    # Side 0 (3 pieces): chain lift hill
    # Slope transitions: FLAT_TO_UP25 -> UP25 -> UP25_TO_FLAT
    coaster.place(TrackElemType.FLAT_TO_UP25, chain_lift=True)
    coaster.place(TrackElemType.UP25, chain_lift=True)
    coaster.place(TrackElemType.UP25_TO_FLAT)
    coaster.place(TrackElemType.RIGHT_QUARTER_TURN3_TILES)

    # Side 1 (5 pieces): flat at height
    for _ in range(5):
        coaster.place(TrackElemType.FLAT)
    coaster.place(TrackElemType.RIGHT_QUARTER_TURN3_TILES)

    # Side 2 (6 pieces): descend back to ground level
    coaster.place(TrackElemType.FLAT_TO_DOWN25)
    coaster.place(TrackElemType.DOWN25)
    coaster.place(TrackElemType.DOWN25_TO_FLAT)
    for _ in range(3):
        coaster.place(TrackElemType.FLAT)
    coaster.place(TrackElemType.RIGHT_QUARTER_TURN3_TILES)

    # Side 3 (5 pieces): flat back to station
    for _ in range(5):
        coaster.place(TrackElemType.FLAT)
    coaster.place(TrackElemType.RIGHT_QUARTER_TURN3_TILES)

    print(f"Pieces: {len(coaster.pieces)}, Circuit: {coaster.circuit_complete}")

    coaster.place_entrance(Tile(101, 99))
    coaster.place_exit(Tile(101, 101))
    coaster.open()
    game.advance_ticks(500)
    print(f"Status: {coaster.data.status}")
