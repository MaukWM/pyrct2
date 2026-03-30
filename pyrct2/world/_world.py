"""WorldProxy — spatial queries on the game map."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, TypeAdapter

from pyrct2._generated.state import TileElement
from pyrct2.world._tile import Tile

if TYPE_CHECKING:
    from pyrct2.client import RCT2

_tile_element_adapter: TypeAdapter[TileElement] = TypeAdapter(TileElement)


class MapBounds(BaseModel):
    """Map dimensions in tiles."""

    model_config = ConfigDict(frozen=True)

    x: int
    y: int


class TileData(BaseModel):
    """A tile's full element stack as returned by the bridge."""

    x: int
    y: int
    elements: list[TileElement]


class WorldProxy:
    """Spatial queries: ``game.world``."""

    def __init__(self, client: RCT2) -> None:
        self._client = client

    def get_bounds(self) -> MapBounds:
        """Map dimensions in tiles."""
        raw = self._client._query("get_map_size")
        return MapBounds(x=raw["x"], y=raw["y"])

    def get_tile(self, tile: Tile) -> TileData:
        """Fetch a tile's full element stack."""
        raw = self._client._query("get_tile", {"x": tile.x, "y": tile.y})
        return TileData(
            x=raw["x"],
            y=raw["y"],
            elements=[_tile_element_adapter.validate_python(e) for e in raw["elements"]],
        )

    def get_tiles(self, from_tile: Tile, to_tile: Tile) -> list[TileData]:
        """Fetch all tiles in a rectangular region (inclusive).

        Much faster than individual get_tile() calls due to single TCP round-trip.
        """
        raw_tiles = self._client._query(
            "get_tiles",
            {
                "x1": from_tile.x,
                "y1": from_tile.y,
                "x2": to_tile.x,
                "y2": to_tile.y,
            },
        )
        return [
            TileData(
                x=t["x"],
                y=t["y"],
                elements=[_tile_element_adapter.validate_python(e) for e in t["elements"]],
            )
            for t in raw_tiles
        ]
