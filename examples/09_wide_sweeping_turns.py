"""Wide sweeping turns — compact coaster with 5-tile turns.

Creates a Twister RC using LEFT_QUARTER_TURN5_TILES for wide sweeping turns.
The L5 circuit formula for stn=3 is [0, 3, 3, 3] — the station fills side 0
entirely, so no extra flats are needed on that side.

Run with:
    cd pyrct2 && uv run python examples/09_wide_sweeping_turns.py
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

    # L5 circuit with stn=3: [0, 3, 3, 3] flats per side
    # Side 0: station fills it, go straight to turn
    coaster.place(TrackElemType.LEFT_QUARTER_TURN5_TILES)

    # Sides 1-3: 3 flats each + L5 turn
    for _ in range(3):
        for _ in range(3):
            coaster.place(TrackElemType.FLAT)
        coaster.place(TrackElemType.LEFT_QUARTER_TURN5_TILES)

    print(f"Pieces: {len(coaster.pieces)}, Circuit: {coaster.circuit_complete}")

    coaster.place_entrance(Tile(101, 99))
    coaster.place_exit(Tile(101, 101))
    coaster.open()
    game.advance_ticks(500)
    print(f"Status: {coaster.data.status}")
