"""Tests for slope bitmask decoding."""

import pytest

from pyrct2.world import Tile, decode_slope
from pyrct2.world._slope import LAND_HEIGHT_STEP

# Arbitrary base height for unit tests.
# baseZ=112 → 112 / 16 = land step 7.
BASE_Z = 112
BASE_LEVEL = BASE_Z // LAND_HEIGHT_STEP  # 7


def test_flat():
    h = decode_slope(base_z=BASE_Z, slope=0)
    assert h.is_flat
    assert h.n == h.e == h.s == h.w == BASE_LEVEL


@pytest.mark.parametrize(
    "slope, raised_corner",
    [
        (1, "n"),
        (2, "e"),
        (4, "s"),
        (8, "w"),
    ],
)
def test_single_corner_up(slope, raised_corner):
    """Each bit (0-3) raises exactly one corner by 1 land step."""
    h = decode_slope(base_z=BASE_Z, slope=slope)
    for corner in ("n", "e", "s", "w"):
        expected = BASE_LEVEL + 1 if corner == raised_corner else BASE_LEVEL
        assert getattr(h, corner) == expected, f"corner {corner} for slope={slope}"


def test_decode_flat_tile(game):
    """Flat tile decodes to equal corners."""
    tile = game.world.get_tile(Tile(x=26, y=26))
    h = decode_slope(tile.surface.baseZ, tile.surface.slope)
    assert h.is_flat


def test_decode_sloped_tile(game):
    """Set a slope via terraform and verify decode matches."""
    game.park.cheats.build_in_pause_mode()
    base = game.world.get_tile(Tile(x=26, y=26)).surface.baseHeight

    # TODO: Replace with world.terraform() when available. Currently uses raw
    # action with world coords (tile * 32). style is the slope bitmask from
    # Slope.h: 1=N, 2=E, 4=S, 8=W corner up. No enum available yet.
    STYLE_N_CORNER_UP = 1
    game.actions.land_set_height(x=20 * 32, y=20 * 32, height=base, style=STYLE_N_CORNER_UP)
    tile = game.world.get_tile(Tile(x=20, y=20))

    h = decode_slope(tile.surface.baseZ, tile.surface.slope)
    assert h.n > h.s
    assert h.n == h.s + 1
