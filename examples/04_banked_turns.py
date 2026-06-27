"""Banked turns coaster — banking with sweeping 5-tile turns.

Creates a Twister RC using banked 5-tile turns. Banking adds lateral force
and makes turns look smoother. Demonstrates the bank enter/exit pattern
and wide turns.

Run with:
    cd pyrct2 && uv run python examples/04_banked_turns.py
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

    # Banked turns use a 3-piece pattern:
    #   FLAT_TO_LEFT_BANK -> BANKED_LEFT_QUARTER_TURN5_TILES -> LEFT_BANK_TO_FLAT
    #
    # L5 banked turns occupy more tiles than L3, so the circuit formula changes.
    # L3 formula [n-2, m, n+1, m] with stn=3, n=5, m=5 -> [3, 5, 6, 5]
    # Each banked L5 turn replaces an L3 turn slot but adds 2 extra pieces
    # (the bank enter/exit).

    # Side 0 (3 pieces): chain lift climb
    coaster.place(TrackElemType.FLAT_TO_UP25, chain_lift=True)
    coaster.place(TrackElemType.UP25, chain_lift=True)
    coaster.place(TrackElemType.UP25_TO_FLAT)
    # Banked left turn
    coaster.place(TrackElemType.FLAT_TO_LEFT_BANK)
    coaster.place(TrackElemType.BANKED_LEFT_QUARTER_TURN5_TILES)
    coaster.place(TrackElemType.LEFT_BANK_TO_FLAT)

    # Side 1 (5 pieces): flat at height
    for _ in range(5):
        coaster.place(TrackElemType.FLAT)
    # Banked left turn
    coaster.place(TrackElemType.FLAT_TO_LEFT_BANK)
    coaster.place(TrackElemType.BANKED_LEFT_QUARTER_TURN5_TILES)
    coaster.place(TrackElemType.LEFT_BANK_TO_FLAT)

    # Side 2 (6 pieces): descent + brakes
    coaster.place(TrackElemType.FLAT_TO_DOWN25)
    coaster.place(TrackElemType.DOWN25)
    coaster.place(TrackElemType.DOWN25_TO_FLAT)
    coaster.place(TrackElemType.BRAKES)
    coaster.place(TrackElemType.FLAT)
    coaster.place(TrackElemType.FLAT)
    # Banked left turn
    coaster.place(TrackElemType.FLAT_TO_LEFT_BANK)
    coaster.place(TrackElemType.BANKED_LEFT_QUARTER_TURN5_TILES)
    coaster.place(TrackElemType.LEFT_BANK_TO_FLAT)

    # Side 3 (5 pieces): flat back
    for _ in range(5):
        coaster.place(TrackElemType.FLAT)
    # Banked left turn
    coaster.place(TrackElemType.FLAT_TO_LEFT_BANK)
    coaster.place(TrackElemType.BANKED_LEFT_QUARTER_TURN5_TILES)
    coaster.place(TrackElemType.LEFT_BANK_TO_FLAT)

    print(f"Pieces: {len(coaster.pieces)}, Circuit: {coaster.circuit_complete}")

    coaster.place_entrance(Tile(101, 99))
    coaster.place_exit(Tile(101, 101))
    coaster.open()
    game.advance_ticks(500)
    print(f"Status: {coaster.data.status}")
