"""Integration tests: verify _compute_footprint matches actual game placement.

For each footprint size category, places a ride in the game and scans the map
to confirm the tiles with track elements match the computed footprint exactly.

Covers all 6 footprint sizes × 4 directions, plus track type variants (A/B/C)
where multiple track types exist for the same dimensions.

Track type variants per footprint size:
  1x1: flatTrack1x1A (262) — Balloon Stall
        flatTrack1x1B (264) — Information Kiosk
  2x2: flatTrack2x2 (258) — Spiral Slide
  3x3: flatTrack3x3 (266) — Merry-Go-Round
  4x4: flatTrack4x4 (259) — Bumper Cars
  1x4: flatTrack1x4A (257) — Magic Carpet
        flatTrack1x4B (263) — Swinging Inverter Ship
        flatTrack1x4C (265) — Ferris Wheel
  1x5: flatTrack1x5 (261) — Pirate Ship
"""

import pytest

from pyrct2._generated.enums import Direction
from pyrct2._generated.objects import RideObjects
from pyrct2.rides import _adjacent_tiles, _compute_footprint
from pyrct2.world import Tile


# Center placement tile — far enough from edges for all footprints + scan radius.
CENTER = Tile(26, 26)
SCAN_RADIUS = 6


def _pick_entrance_exit(footprint: set[Tile]) -> tuple[Tile, Tile]:
    """Pick entrance (max y) and exit (min y) from tiles adjacent to the footprint."""
    adjacent = sorted(_adjacent_tiles(footprint), key=lambda t: (t.y, t.x))
    return adjacent[-1], adjacent[0]


def _actual_footprint(game, ride_id: int) -> set[Tile]:
    """Scan the map and return tiles that have track elements for the given ride."""
    from_tile = Tile(CENTER.x - SCAN_RADIUS, CENTER.y - SCAN_RADIUS)
    to_tile = Tile(CENTER.x + SCAN_RADIUS, CENTER.y + SCAN_RADIUS)
    result = set()
    for td in game.world.get_tiles(from_tile, to_tile):
        for track in td.tracks:
            if track.ride == ride_id:
                result.add(Tile(td.x, td.y))
    return result


def _place_and_check(game, obj, direction):
    """Place a ride, compare actual vs computed footprint, then demolish."""
    computed = set(_compute_footprint(obj, CENTER, direction))

    if not game.objects.is_loaded(obj):
        game.objects.load(obj)

    category = obj.category if isinstance(obj.category, str) else obj.category[0]
    if category == "stall":
        ride_id = game.rides.place_stall(obj=obj, tile=CENTER, direction=direction)
    else:
        entrance, exit_tile = _pick_entrance_exit(computed)
        ride_id = game.rides.place_flat_ride(
            obj=obj,
            tile=CENTER,
            entrance=entrance,
            exit=exit_tile,
            direction=direction,
        )

    actual = _actual_footprint(game, ride_id)
    game.rides.demolish(ride_id)

    assert actual == computed, (
        f"{obj.name} direction={direction.name}: "
        f"computed={sorted((t.x, t.y) for t in computed)}, "
        f"actual={sorted((t.x, t.y) for t in actual)}"
    )


# ── 1x1A: Balloon Stall (flatTrack1x1A = 262) ──────────────────────


def test_footprint_1x1a(game):
    game.park.cheats.build_in_pause_mode()
    for d in Direction:
        _place_and_check(game, RideObjects.stall.BALLOON_STALL, d)


# ── 1x1B: Information Kiosk (flatTrack1x1B = 264) ───────────────────


def test_footprint_1x1b(game):
    game.park.cheats.build_in_pause_mode()
    for d in Direction:
        _place_and_check(game, RideObjects.stall.INFORMATION_KIOSK, d)


# ── 2x2: Spiral Slide (flatTrack2x2 = 258) ──────────────────────────


@pytest.mark.parametrize("direction", list(Direction), ids=lambda d: d.name)
def test_footprint_2x2(game, direction):
    game.park.cheats.build_in_pause_mode()
    _place_and_check(game, RideObjects.gentle.SPIRAL_SLIDE, direction)


# ── 3x3: Merry-Go-Round (flatTrack3x3 = 266) ────────────────────────


def test_footprint_3x3(game):
    game.park.cheats.build_in_pause_mode()
    for d in Direction:
        _place_and_check(game, RideObjects.gentle.MERRY_GO_ROUND, d)


# ── 4x4: Bumper Cars (flatTrack4x4 = 259) ────────────────────────────


@pytest.mark.parametrize("direction", list(Direction), ids=lambda d: d.name)
def test_footprint_4x4(game, direction):
    game.park.cheats.build_in_pause_mode()
    _place_and_check(game, RideObjects.gentle.BUMPER_CARS, direction)


# ── 1x4A: Magic Carpet (flatTrack1x4A = 257) ─────────────────────────


@pytest.mark.parametrize("direction", list(Direction), ids=lambda d: d.name)
def test_footprint_1x4a(game, direction):
    game.park.cheats.build_in_pause_mode()
    _place_and_check(game, RideObjects.thrill.MAGIC_CARPET, direction)


# ── 1x4B: Swinging Inverter Ship (flatTrack1x4B = 263) ───────────────


@pytest.mark.parametrize("direction", list(Direction), ids=lambda d: d.name)
def test_footprint_1x4b(game, direction):
    game.park.cheats.build_in_pause_mode()
    _place_and_check(game, RideObjects.thrill.SWINGING_INVERTER_SHIP, direction)


# ── 1x4C: Ferris Wheel (flatTrack1x4C = 265) ─────────────────────────


@pytest.mark.parametrize("direction", list(Direction), ids=lambda d: d.name)
def test_footprint_1x4c(game, direction):
    game.park.cheats.build_in_pause_mode()
    _place_and_check(game, RideObjects.gentle.FERRIS_WHEEL, direction)


# ── 1x5: Pirate Ship (flatTrack1x5 = 261) ────────────────────────────


@pytest.mark.parametrize("direction", list(Direction), ids=lambda d: d.name)
def test_footprint_1x5(game, direction):
    game.park.cheats.build_in_pause_mode()
    _place_and_check(game, RideObjects.thrill.PIRATE_SHIP, direction)
