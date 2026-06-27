"""Log flume — a water ride circuit.

Creates a Log Flume with a hill and splash-down. Demonstrates that
create_tracked_ride() works for all tracked ride types, not just coasters.
Water rides, transport rides, and tracked gentle rides all use the same API.

Run with:
    cd pyrct2 && uv run python examples/07_log_flume.py
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

    flume = game.rides.create_tracked_ride(
        obj=RideObjects.water.LOGS,
        station_origin=Tile(100, 100),
        station_length=3,
        direction=Direction.EAST,
    )

    # L3 turns, stn=3: [n-2, m, n+1, m] with n=5, m=5 -> [3, 5, 6, 5]

    # Side 0 (3 pieces): climb
    flume.place(TrackElemType.FLAT_TO_UP25)
    flume.place(TrackElemType.UP25)
    flume.place(TrackElemType.UP25_TO_FLAT)
    flume.place(TrackElemType.LEFT_QUARTER_TURN3_TILES)

    # Side 1 (5 pieces): flat at height
    for _ in range(5):
        flume.place(TrackElemType.FLAT)
    flume.place(TrackElemType.LEFT_QUARTER_TURN3_TILES)

    # Side 2 (6 pieces): drop back to ground
    flume.place(TrackElemType.FLAT_TO_DOWN25)
    flume.place(TrackElemType.DOWN25)
    flume.place(TrackElemType.DOWN25_TO_FLAT)
    for _ in range(3):
        flume.place(TrackElemType.FLAT)
    flume.place(TrackElemType.LEFT_QUARTER_TURN3_TILES)

    # Side 3 (5 pieces): flat back to station
    for _ in range(5):
        flume.place(TrackElemType.FLAT)
    flume.place(TrackElemType.LEFT_QUARTER_TURN3_TILES)

    print(f"Pieces: {len(flume.pieces)}, Circuit: {flume.circuit_complete}")

    flume.place_entrance(Tile(101, 99))
    flume.place_exit(Tile(101, 101))
    flume.open()
    game.advance_ticks(500)
    print(f"Status: {flume.data.status}")
