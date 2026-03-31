"""Slope bitmask decoding — convert slope integers to corner heights.

OpenRCT2 encodes terrain slope as a 5-bit integer on each SurfaceElement.
Bits 0-3 indicate which corners are raised; bit 4 is a diagonal modifier
that creates steep slopes (double-height corners).

This module ports the exact lookup table from the OpenRCT2 C++ source to
provide corner height resolution in Python.

Source references (OpenRCT2 v0.4.32):
  Slope constants:
    https://github.com/OpenRCT2/OpenRCT2/blob/v0.4.32/src/openrct2/world/tile_element/Slope.h#L18-L25
  Corner height lookup table + GetSlopeCornerHeights():
    https://github.com/OpenRCT2/OpenRCT2/blob/v0.4.32/src/openrct2/world/tile_element/Slope.cpp#L19-L68
  Height step constants (kCoordsZStep=8, kLandHeightStep=16):
    https://github.com/OpenRCT2/OpenRCT2/blob/v0.4.32/src/openrct2/world/MapLimits.h#L16-L32

Bitmask layout:
    Bit 0 = North corner raised   (kTileSlopeNCornerUp = 0b00001)
    Bit 1 = East corner raised    (kTileSlopeECornerUp = 0b00010)
    Bit 2 = South corner raised   (kTileSlopeSCornerUp = 0b00100)
    Bit 3 = West corner raised    (kTileSlopeWCornerUp = 0b01000)
    Bit 4 = Diagonal flag         (kTileSlopeDiagonalFlag = 0b10000)

The C++ source stores corner offsets as {top, right, bottom, left} in
screen/isometric coordinates. GetSlopeCornerHeights() maps these to
compass directions:
    top    → South
    right  → West
    bottom → North
    left   → East
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

# One land increment in z-coordinate units.
# kLandHeightStep = 2 * kCoordsZStep = 2 * 8 = 16
# https://github.com/OpenRCT2/OpenRCT2/blob/v0.4.32/src/openrct2/world/MapLimits.h#L32
LAND_HEIGHT_STEP: int = 16

# Slope bitmask constants for use with set_height(slope=...).
# https://github.com/OpenRCT2/OpenRCT2/blob/v0.4.32/src/openrct2/world/tile_element/Slope.h#L18-L24
SLOPE_FLAT: int = 0
SLOPE_N: int = 1
SLOPE_E: int = 2
SLOPE_S: int = 4
SLOPE_W: int = 8
SLOPE_DIAGONAL: int = 16


class CornerHeights(BaseModel):
    """Height at each corner of a tile, in land steps (not raw z-units).

    One land step = LAND_HEIGHT_STEP (16) z-units. This matches the
    vertical grid — just like Tile abstracts world coords into tile coords,
    CornerHeights abstracts z-units into land steps.

    Computed from SurfaceElement.baseZ + slope-dependent offsets.
    """

    model_config = ConfigDict(frozen=True)

    n: int
    e: int
    s: int
    w: int

    @property
    def max(self) -> int:
        """Highest corner in land steps."""
        return max(self.n, self.e, self.s, self.w)

    @property
    def min(self) -> int:
        """Lowest corner in land steps."""
        return min(self.n, self.e, self.s, self.w)

    @property
    def is_flat(self) -> bool:
        return self.n == self.e == self.s == self.w


# ── Lookup table ──────────────────────────────────────────────────────
#
# Ported from kSlopeRelativeCornerHeights in Slope.cpp.
# Each tuple is (north, east, south, west) corner offset in land increments.
# Multiply by LAND_HEIGHT_STEP (16) to get z-unit offsets.
#
# The C++ source stores {top, right, bottom, left} (screen coords).
# GetSlopeCornerHeights() maps: bottom→N, left→E, top→S, right→W.
# We store (N, E, S, W) directly here to skip the mapping at runtime.
#
# Index = slope value (0-31). Values 0-15 are non-diagonal, 16-31 have
# the diagonal flag set (bit 4).
#
# https://github.com/OpenRCT2/OpenRCT2/blob/v0.4.32/src/openrct2/world/tile_element/Slope.cpp#L19-L52

_CORNER_OFFSETS: tuple[tuple[int, int, int, int], ...] = (
    #  N  E  S  W     slope  description
    (0, 0, 0, 0),  #  0     flat
    (1, 0, 0, 0),  #  1     N corner up
    (0, 1, 0, 0),  #  2     E corner up
    (1, 1, 0, 0),  #  3     NE side up
    (0, 0, 1, 0),  #  4     S corner up
    (1, 0, 1, 0),  #  5     NS valley
    (0, 1, 1, 0),  #  6     SE side up
    (1, 1, 1, 0),  #  7     W corner down (3 up)
    (0, 0, 0, 1),  #  8     W corner up
    (1, 0, 0, 1),  #  9     NW side up
    (0, 1, 0, 1),  #  10    WE valley
    (1, 1, 0, 1),  #  11    S corner down (3 up)
    (0, 0, 1, 1),  #  12    SW side up
    (1, 0, 1, 1),  #  13    E corner down (3 up)
    (0, 1, 1, 1),  #  14    N corner down (3 up)
    (1, 1, 1, 1),  #  15    all corners up (flat raised)
    (0, 0, 0, 0),  #  16    diag flat (unused)
    (1, 0, 0, 0),  #  17    diag N up
    (0, 1, 0, 0),  #  18    diag E up
    (1, 1, 0, 0),  #  19    diag NE side
    (0, 0, 1, 0),  #  20    diag S up
    (1, 0, 1, 0),  #  21    diag NS valley
    (0, 1, 1, 0),  #  22    diag SE side
    (1, 2, 1, 0),  #  23    diag W down (steep)
    (0, 0, 0, 1),  #  24    diag W up
    (1, 0, 0, 1),  #  25    diag NW side
    (0, 1, 0, 1),  #  26    diag WE valley
    (2, 1, 0, 1),  #  27    diag S down (steep)
    (0, 0, 1, 1),  #  28    diag SW side
    (1, 0, 1, 2),  #  29    diag E down (steep)
    (0, 1, 2, 1),  #  30    diag N down (steep)
    (1, 1, 1, 1),  #  31    diag all up
)


def decode_slope(base_z: int, slope: int) -> CornerHeights:
    """Compute absolute z-coordinate at each corner of a sloped tile.

    Args:
        base_z: The SurfaceElement.baseZ value (z-coordinate units).
        slope: The SurfaceElement.slope value (0-31 bitmask).

    Returns:
        CornerHeights with absolute z-values at N, E, S, W corners.

    The slope bitmask encodes which corners are raised above baseZ.
    Each raised corner adds LAND_HEIGHT_STEP (16) z-units, except for
    steep diagonal slopes (slopes 23, 27, 29, 30) where one corner is
    raised by 2 * LAND_HEIGHT_STEP (32).

    Source: GetSlopeCornerHeights() in OpenRCT2 Slope.cpp
    https://github.com/OpenRCT2/OpenRCT2/blob/v0.4.32/src/openrct2/world/tile_element/Slope.cpp#L60-L68
    """
    base_level = base_z // LAND_HEIGHT_STEP
    offsets = _CORNER_OFFSETS[slope & 0x1F]
    return CornerHeights(
        n=base_level + offsets[0],
        e=base_level + offsets[1],
        s=base_level + offsets[2],
        w=base_level + offsets[3],
    )
