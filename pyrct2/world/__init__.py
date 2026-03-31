"""Spatial abstraction layer — tile coordinates and world queries."""

from pyrct2.world._slope import (
    LAND_HEIGHT_STEP,
    SLOPE_DIAGONAL,
    SLOPE_E,
    SLOPE_FLAT,
    SLOPE_N,
    SLOPE_S,
    SLOPE_W,
    CornerHeights,
    decode_slope,
)
from pyrct2.world._tile import TILE_SIZE, Tile
from pyrct2.world._world import MapBounds, TileData, WorldProxy

__all__ = [
    "LAND_HEIGHT_STEP",
    "SLOPE_DIAGONAL",
    "SLOPE_E",
    "SLOPE_FLAT",
    "SLOPE_N",
    "SLOPE_S",
    "SLOPE_W",
    "CornerHeights",
    "MapBounds",
    "TILE_SIZE",
    "Tile",
    "TileData",
    "WorldProxy",
    "decode_slope",
]
