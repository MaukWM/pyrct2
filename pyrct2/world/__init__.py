"""Spatial abstraction layer — tile coordinates and world queries."""

from pyrct2.world._tile import TILE_SIZE, Tile
from pyrct2.world._world import MapBounds, TileData, WorldProxy

__all__ = ["TILE_SIZE", "Tile", "MapBounds", "TileData", "WorldProxy"]
