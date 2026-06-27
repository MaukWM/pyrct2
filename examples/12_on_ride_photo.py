"""On-ride photo and brakes — special flat pieces.

Creates a Junior RC with an on-ride photo section and brakes.
On-ride photos generate extra income. Brakes slow the train before the station.

Run with:
    cd pyrct2 && uv run python examples/12_on_ride_photo.py
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

    # L3 turns, stn=3: [3, 5, 6, 5]

    # Side 0: chain lift hill
    coaster.place(TrackElemType.FLAT_TO_UP25, chain_lift=True)
    coaster.place(TrackElemType.UP25, chain_lift=True)
    coaster.place(TrackElemType.UP25_TO_FLAT)
    coaster.place(TrackElemType.LEFT_QUARTER_TURN3_TILES)

    # Side 1: flat with on-ride photo
    coaster.place(TrackElemType.FLAT)
    coaster.place(TrackElemType.ON_RIDE_PHOTO)
    coaster.place(TrackElemType.FLAT)
    coaster.place(TrackElemType.FLAT)
    coaster.place(TrackElemType.FLAT)
    coaster.place(TrackElemType.LEFT_QUARTER_TURN3_TILES)

    # Side 2: descent
    coaster.place(TrackElemType.FLAT_TO_DOWN25)
    coaster.place(TrackElemType.DOWN25)
    coaster.place(TrackElemType.DOWN25_TO_FLAT)
    coaster.place(TrackElemType.FLAT)
    coaster.place(TrackElemType.FLAT)
    coaster.place(TrackElemType.FLAT)
    coaster.place(TrackElemType.LEFT_QUARTER_TURN3_TILES)

    # Side 3: brakes before station
    coaster.place(TrackElemType.FLAT)
    coaster.place(TrackElemType.FLAT)
    coaster.place(TrackElemType.BRAKES)
    coaster.place(TrackElemType.FLAT)
    coaster.place(TrackElemType.FLAT)
    coaster.place(TrackElemType.LEFT_QUARTER_TURN3_TILES)

    print(f"Pieces: {len(coaster.pieces)}, Circuit: {coaster.circuit_complete}")

    coaster.place_entrance(Tile(101, 99))
    coaster.place_exit(Tile(101, 101))
    coaster.open()
    game.advance_ticks(500)
    print(f"Status: {coaster.data.status}")
