"""Tile coordinate type and spatial constants.

OpenRCT2 uses world units internally (32 per tile). The high-level API
works in tile coordinates exclusively. This module provides the Tile type
for grid-level spatial reasoning and conversion to/from world units.

Reference: kCoordsXYStep in OpenRCT2 C++ source
https://github.com/OpenRCT2/OpenRCT2/blob/develop/src/openrct2/world/MapLimits.h
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

# World units per tile — hardcoded in OpenRCT2 as kCoordsXYStep, unchanged since original RCT2.
# See: https://github.com/OpenRCT2/OpenRCT2/blob/develop/src/openrct2/world/MapLimits.h
TILE_SIZE: int = 32


class Tile(BaseModel):
    """A tile coordinate on the game grid.

    Supports both ``Tile(3, 7)`` and ``Tile(x=3, y=7)``.
    Frozen (immutable + hashable) so it can be used as a dict key or in sets.
    """

    model_config = ConfigDict(frozen=True)

    x: int
    y: int

    def __init__(self, *args: int, **kwargs: int) -> None:
        if args:
            super().__init__(x=args[0], y=args[1] if len(args) > 1 else 0, **kwargs)
        else:
            super().__init__(**kwargs)

    def to_world(self) -> tuple[int, int]:
        """World coords at tile origin (northwest corner)."""
        return (self.x * TILE_SIZE, self.y * TILE_SIZE)

    def to_world_center(self) -> tuple[int, int]:
        """World coords at tile center."""
        return (self.x * TILE_SIZE + TILE_SIZE // 2, self.y * TILE_SIZE + TILE_SIZE // 2)

    @staticmethod
    def from_world(wx: int, wy: int) -> Tile:
        """Floor world coords to tile."""
        return Tile(x=wx // TILE_SIZE, y=wy // TILE_SIZE)

    def distance_to(self, other: Tile) -> int:
        """Manhattan distance in tiles."""
        return abs(self.x - other.x) + abs(self.y - other.y)

    def offset(self, dx: int, dy: int) -> Tile:
        """Tile relative to this one."""
        return Tile(x=self.x + dx, y=self.y + dy)

    def __str__(self) -> str:
        return f"Tile({self.x}, {self.y})"

    def __repr__(self) -> str:
        return f"Tile(x={self.x}, y={self.y})"
