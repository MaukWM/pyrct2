"""Mini railway — a transport ride loop.

Creates a Miniature Railway with a large flat circuit.
Transport rides use the same tracked ride API as coasters.

Run with:
    cd pyrct2 && uv run python examples/08_mini_railway.py
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

    railway = game.rides.create_tracked_ride(
        obj=RideObjects.transport.AMERICAN_STYLE_STEAM_TRAINS,
        station_origin=Tile(100, 100),
        station_length=3,
        direction=Direction.EAST,
    )

    # Large scenic loop with R3 turns
    # stn=3: [n-2, m, n+1, m] with n=10, m=8 -> [8, 8, 11, 8]
    flats_per_side = [8, 8, 11, 8]
    for side in range(4):
        for _ in range(flats_per_side[side]):
            railway.place(TrackElemType.FLAT)
        railway.place(TrackElemType.RIGHT_QUARTER_TURN3_TILES)

    print(f"Pieces: {len(railway.pieces)}, Circuit: {railway.circuit_complete}")

    railway.place_entrance(Tile(101, 99))
    railway.place_exit(Tile(101, 101))
    railway.open()
    game.advance_ticks(500)
    print(f"Status: {railway.data.status}")
