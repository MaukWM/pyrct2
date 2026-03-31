"""WorldProxy — spatial queries on the game map."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, TypeAdapter

from pyrct2._generated.enums import MapSelectType
from pyrct2._generated.state import (
    BannerElement,
    EntranceElement,
    FootpathElement,
    LargeSceneryElement,
    SmallSceneryElement,
    SurfaceElement,
    TileElement,
    TrackElement,
    WallElement,
)
from pyrct2.result import ActionResult
from pyrct2.world._slope import CornerHeights, decode_slope
from pyrct2.world._tile import TILE_SIZE, Tile

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

    @property
    def surface(self) -> SurfaceElement:
        """The surface element (exactly one per tile)."""
        surfaces = [e for e in self.elements if isinstance(e, SurfaceElement)]
        assert len(surfaces) == 1, f"Expected 1 surface element at ({self.x}, {self.y}), found {len(surfaces)}"
        return surfaces[0]

    @property
    def corner_heights(self) -> CornerHeights:
        """Height at each corner in land steps, accounting for slope."""
        return decode_slope(self.surface.baseZ, self.surface.slope)

    @property
    def paths(self) -> list[FootpathElement]:
        return [e for e in self.elements if isinstance(e, FootpathElement)]

    @property
    def tracks(self) -> list[TrackElement]:
        return [e for e in self.elements if isinstance(e, TrackElement)]

    @property
    def scenery(self) -> list[SmallSceneryElement | LargeSceneryElement]:
        return [e for e in self.elements if isinstance(e, (SmallSceneryElement, LargeSceneryElement))]

    @property
    def walls(self) -> list[WallElement]:
        return [e for e in self.elements if isinstance(e, WallElement)]

    @property
    def entrances(self) -> list[EntranceElement]:
        return [e for e in self.elements if isinstance(e, EntranceElement)]

    @property
    def banners(self) -> list[BannerElement]:
        return [e for e in self.elements if isinstance(e, BannerElement)]


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
        x1 = min(from_tile.x, to_tile.x)
        y1 = min(from_tile.y, to_tile.y)
        x2 = max(from_tile.x, to_tile.x)
        y2 = max(from_tile.y, to_tile.y)
        raw_tiles = self._client._query(
            "get_tiles",
            {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
        )
        return [
            TileData(
                x=t["x"],
                y=t["y"],
                elements=[_tile_element_adapter.validate_python(e) for e in t["elements"]],
            )
            for t in raw_tiles
        ]

    def max_corner_height(self, from_tile: Tile, to_tile: Tile) -> int:
        """Highest corner height (land steps) across a rectangular region."""
        tiles = self.get_tiles(from_tile, to_tile)
        return max(t.corner_heights.max for t in tiles)

    def is_area_flat(self, from_tile: Tile, to_tile: Tile) -> bool:
        """Whether all corners across a rectangular region are at the same height."""
        tiles = self.get_tiles(from_tile, to_tile)
        heights = {
            h for t in tiles for h in (t.corner_heights.n, t.corner_heights.e, t.corner_heights.s, t.corner_heights.w)
        }
        return len(heights) == 1

    # ── Terraform ─────────────────────────────────────────────────────

    def set_height(self, tile: Tile, height: int, slope: int = 0) -> ActionResult:
        """Set a tile to an exact height (land steps) and slope.

        Args:
            tile: The tile to modify.
            height: Target height in land steps (not z-units).
            slope: Slope bitmask (0=flat, 1=N, 2=E, 4=S, 8=W, 16=diagonal).
        """
        # The action takes baseHeight units (2 per land step).
        base_height = height * 2
        return ActionResult.from_response(
            self._client.actions.land_set_height(
                x=tile.x * TILE_SIZE,
                y=tile.y * TILE_SIZE,
                height=base_height,
                style=slope,
            )
        )

    def raise_land(
        self,
        from_tile: Tile,
        to_tile: Tile | None = None,
        selection_type: MapSelectType = MapSelectType.FULL,
    ) -> ActionResult:
        """Raise terrain by one land step. No neighbor smoothing.

        Each tile in the area is raised independently — this can create
        sharp cliffs at the edges. Use raise_land_smooth() for game-UI-like
        behavior with automatic slope transitions.

        Valid selection_types: FULL, CORNER0-3 (N/E/S/W), EDGE0-3 (SW/NW/NE/SE).
        """
        to_tile = to_tile or from_tile
        x1 = min(from_tile.x, to_tile.x) * TILE_SIZE
        y1 = min(from_tile.y, to_tile.y) * TILE_SIZE
        x2 = max(from_tile.x, to_tile.x) * TILE_SIZE
        y2 = max(from_tile.y, to_tile.y) * TILE_SIZE
        return ActionResult.from_response(
            self._client.actions.land_raise(
                x=x1,
                y=y1,
                x1=x1,
                y1=y1,
                x2=x2,
                y2=y2,
                selection_type=selection_type,
            )
        )

    def lower_land(
        self,
        from_tile: Tile,
        to_tile: Tile | None = None,
        selection_type: MapSelectType = MapSelectType.FULL,
    ) -> ActionResult:
        """Lower terrain by one land step. No neighbor smoothing.

        See raise_land() for details. Use lower_land_smooth() for
        game-UI-like behavior.
        """
        to_tile = to_tile or from_tile
        x1 = min(from_tile.x, to_tile.x) * TILE_SIZE
        y1 = min(from_tile.y, to_tile.y) * TILE_SIZE
        x2 = max(from_tile.x, to_tile.x) * TILE_SIZE
        y2 = max(from_tile.y, to_tile.y) * TILE_SIZE
        return ActionResult.from_response(
            self._client.actions.land_lower(
                x=x1,
                y=y1,
                x1=x1,
                y1=y1,
                x2=x2,
                y2=y2,
                selection_type=selection_type,
            )
        )

    def raise_land_smooth(
        self,
        from_tile: Tile,
        to_tile: Tile | None = None,
        selection_type: MapSelectType = MapSelectType.FULL,
    ) -> ActionResult:
        """Raise terrain by one land step with neighbor smoothing.

        Behaves like the in-game raise tool: raises the area and
        automatically creates slope transitions on neighboring tiles
        to avoid cliffs.

        Valid selection_types: FULL, CORNER0-3 (N/E/S/W), EDGE0-3 (SW/NW/NE/SE).
        """
        to_tile = to_tile or from_tile
        x1 = min(from_tile.x, to_tile.x) * TILE_SIZE
        y1 = min(from_tile.y, to_tile.y) * TILE_SIZE
        x2 = max(from_tile.x, to_tile.x) * TILE_SIZE
        y2 = max(from_tile.y, to_tile.y) * TILE_SIZE
        return ActionResult.from_response(
            self._client.actions.land_smooth(
                x=x1,
                y=y1,
                x1=x1,
                y1=y1,
                x2=x2,
                y2=y2,
                selection_type=selection_type,
                is_lowering=False,
            )
        )

    def lower_land_smooth(
        self,
        from_tile: Tile,
        to_tile: Tile | None = None,
        selection_type: MapSelectType = MapSelectType.FULL,
    ) -> ActionResult:
        """Lower terrain by one land step with neighbor smoothing.

        See raise_land_smooth() for details.
        """
        to_tile = to_tile or from_tile
        x1 = min(from_tile.x, to_tile.x) * TILE_SIZE
        y1 = min(from_tile.y, to_tile.y) * TILE_SIZE
        x2 = max(from_tile.x, to_tile.x) * TILE_SIZE
        y2 = max(from_tile.y, to_tile.y) * TILE_SIZE
        return ActionResult.from_response(
            self._client.actions.land_smooth(
                x=x1,
                y=y1,
                x1=x1,
                y1=y1,
                x2=x2,
                y2=y2,
                selection_type=selection_type,
                is_lowering=True,
            )
        )
