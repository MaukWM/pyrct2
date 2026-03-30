"""WorldProxy — spatial queries on the game map."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict

from pyrct2.world._tile import Tile

if TYPE_CHECKING:
    from pyrct2.client import RCT2


class MapBounds(BaseModel):
    """Map dimensions in tiles."""

    model_config = ConfigDict(frozen=True)

    width: int
    height: int


class WorldProxy:
    """Spatial queries: ``game.world``."""

    def __init__(self, client: RCT2) -> None:
        self._client = client

    def get_bounds(self) -> MapBounds:
        """Map dimensions in tiles."""
        raw = self._client._query("get_map_size")
        return MapBounds(width=raw["x"], height=raw["y"])

    def get_tile(self, tile: Tile) -> dict[str, Any]:
        """Fetch raw tile data (surface + all stacked elements).

        Returns the bridge payload as-is: {x, y, elements: [...]}.
        A typed TileData model will wrap this in a future version.
        """
        return self._client._query("get_tile", {"x": tile.x, "y": tile.y})

    def get_tiles(self, from_tile: Tile, to_tile: Tile) -> list[dict[str, Any]]:
        """Fetch all tiles in a rectangular region (inclusive).

        Returns a list of raw tile payloads. Much faster than
        individual get_tile() calls due to single TCP round-trip.
        """
        return self._client._query(
            "get_tiles",
            {
                "x1": from_tile.x,
                "y1": from_tile.y,
                "x2": to_tile.x,
                "y2": to_tile.y,
            },
        )
