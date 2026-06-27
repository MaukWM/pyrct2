"""Simple flat oval — the minimal complete coaster.

Creates a Junior RC with a flat rectangular circuit using 3-tile turns.
Demonstrates the basic lifecycle: create -> build -> entrance/exit -> open.

Run with:
    cd pyrct2 && uv run python examples/01_simple_oval.py
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

    # Create a Junior RC with a 3-tile station facing east
    coaster = game.rides.create_tracked_ride(
        obj=RideObjects.rollercoaster.LADYBIRD_TRAINS,
        station_origin=Tile(100, 100),
        station_length=3,
        direction=Direction.EAST,
    )

    # Build a flat rectangular circuit with right 3-tile turns.
    #
    # Circuit geometry for R3 turns with station_length=3:
    #   [n-2, m, n+1, m] flats per side closes the circuit.
    #   Here n=5, m=5 -> [3, 5, 6, 5] flats per side.
    flats_per_side = [3, 5, 6, 5]
    for side in range(4):
        for _ in range(flats_per_side[side]):
            coaster.place(TrackElemType.FLAT)
        coaster.place(TrackElemType.RIGHT_QUARTER_TURN3_TILES)

    print(f"Pieces: {len(coaster.pieces)}, Circuit: {coaster.circuit_complete}")

    # Place entrance and exit adjacent to station
    # Station at Tile(100-102, 100) facing EAST -> entrance/exit on Y-adjacent tiles
    coaster.place_entrance(Tile(101, 99))
    coaster.place_exit(Tile(101, 101))

    # Test and open
    coaster.open()
    game.advance_ticks(500)
    print(f"Status: {coaster.data.status}")
