"""PathsProxy — footpath placement and removal."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyrct2._generated.enums import (
    Direction,
    FootpathSlopeType,
    INVALID_DIRECTION,
    PathConstructFlags,
)
from pyrct2._generated.objects import (
    FootpathAdditionInfo,
    FootpathRailingsInfo,
    FootpathSurfaceInfo,
)
from pyrct2.result import ActionResult
from pyrct2.world._slope import LAND_HEIGHT_STEP
from pyrct2.world._tile import TILE_SIZE, Tile

if TYPE_CHECKING:
    from pyrct2.client import RCT2

# Terrain slope bitmask → (FootpathSlopeType, slopeDirection) mapping.
# Mirrors kDefaultPathSlope[] in OpenRCT2 Footpath.cpp:
# https://github.com/OpenRCT2/OpenRCT2/blob/v0.4.32/src/openrct2/world/Footpath.cpp#L108-L115
# Index = terrain slope (N=1, E=2, S=4, W=8).
# "raise" means flat path placed one land step higher.
# "irregular" means the terrain can't auto-determine a path slope.
_TERRAIN_TO_PATH_SLOPE: list[tuple[FootpathSlopeType, int]] = [
    (FootpathSlopeType.FLAT, 0),  # 0:  flat
    (FootpathSlopeType.IRREGULAR, 0),  # 1:  N
    (FootpathSlopeType.IRREGULAR, 0),  # 2:  E
    (FootpathSlopeType.SLOPED, 2),  # 3:  N+E → slope EAST
    (FootpathSlopeType.IRREGULAR, 0),  # 4:  S
    (FootpathSlopeType.IRREGULAR, 0),  # 5:  N+S (opposite)
    (FootpathSlopeType.SLOPED, 3),  # 6:  E+S → slope SOUTH
    (FootpathSlopeType.RAISE, 0),  # 7:  N+E+S (3 corners)
    (FootpathSlopeType.IRREGULAR, 0),  # 8:  W
    (FootpathSlopeType.SLOPED, 1),  # 9:  N+W → slope NORTH
    (FootpathSlopeType.IRREGULAR, 0),  # 10: E+W (opposite)
    (FootpathSlopeType.RAISE, 0),  # 11: N+E+W
    (FootpathSlopeType.SLOPED, 0),  # 12: S+W → slope WEST
    (FootpathSlopeType.RAISE, 0),  # 13: N+S+W
    (FootpathSlopeType.RAISE, 0),  # 14: E+S+W
    (FootpathSlopeType.IRREGULAR, 0),  # 15: all corners
]


def _resolve_object_index(client: RCT2, obj_type: str, identifier: str) -> int:
    """Resolve a footpath object identifier to its loaded slot index."""
    objects = client._query("get_objects", {"type": obj_type})
    for o in objects:
        if o["identifier"] == identifier:
            return o["index"]
    raise RuntimeError(
        f"{identifier} is not loaded in this scenario. Loaded {obj_type}: {[o['identifier'] for o in objects]}"
    )


def _first_surface_index(client: RCT2, *, queue: bool = False) -> int:
    """Return the index of the first footpath surface matching the queue preference."""
    surfaces = client._query("get_objects", {"type": "footpath_surface"})
    for s in surfaces:
        is_queue = "queue" in s["identifier"]
        if is_queue == queue:
            return s["index"]
    return surfaces[0]["index"]


def _first_railings_index(client: RCT2) -> int:
    """Return the index of the first footpath railings in the scenario."""
    railings = client._query("get_objects", {"type": "footpath_railings"})
    return railings[0]["index"]


class PathsProxy:
    """Footpath placement: ``game.paths``."""

    def __init__(self, client: RCT2) -> None:
        self._client = client
        self._default_surface = _first_surface_index(client)
        self._default_queue_surface = _first_surface_index(client, queue=True)
        self._default_railings = _first_railings_index(client)

    def _resolve_surface(self, surface: FootpathSurfaceInfo | None, *, queue: bool = False) -> int:
        if surface is None:
            return self._default_queue_surface if queue else self._default_surface
        return _resolve_object_index(
            self._client,
            "footpath_surface",
            surface.identifier,
        )

    def _resolve_railings(self, railings: FootpathRailingsInfo | None) -> int:
        if railings is None:
            return self._default_railings
        return _resolve_object_index(
            self._client,
            "footpath_railings",
            railings.identifier,
        )

    def place(
        self,
        tile: Tile,
        *,
        height: int | None = None,
        slope: Direction | None = None,
        queue: bool = False,
        surface: FootpathSurfaceInfo | None = None,
        railings: FootpathRailingsInfo | None = None,
    ) -> ActionResult:
        """Place a footpath with auto-connect.

        When called with no ``height`` or ``slope``, reads the terrain and
        automatically places the right path type — flat on flat ground,
        sloped on 2-adjacent-corner slopes, or flat-raised on 3-corner
        slopes. This matches how the game UI places paths.

        Raises ActionError for irregular terrain (1 corner, opposite corners)
        where the game can't determine a path slope.

        Pass ``height`` and/or ``slope`` explicitly to override terrain
        detection (e.g. for elevated paths or manual slope control).

        Args:
            tile: Where to place the path.
            height: Height in land steps. None = auto-detect from terrain.
            slope: Direction the path rises toward. None = auto-detect.
                When explicit, the path bridges one land step: its low end
                is at ``height`` and its high end is at ``height + 1``.
                Slopes do not connect perpendicular — use a flat landing
                pad for turns.
            queue: If True, place a queue path (auto-selects queue surface).
            surface: Footpath surface. None = scenario default.
            railings: Footpath railings. None = scenario default.
        """
        if height is not None or slope is not None:
            # Manual mode: use explicit values
            z = self._client.world.resolve_height(tile, height)
            if slope is not None:
                s_type = FootpathSlopeType.SLOPED
                s_dir = slope
            else:
                s_type = FootpathSlopeType.FLAT
                s_dir = Direction(0)
        else:
            # Auto mode: detect from terrain
            tile_data = self._client.world.get_tile(tile)
            terrain_slope = tile_data.surface.slope & 0x0F
            base_z = tile_data.surface.baseZ

            s_type, s_dir_int = _TERRAIN_TO_PATH_SLOPE[terrain_slope]
            s_dir = Direction(0)

            if s_type == FootpathSlopeType.RAISE:
                s_type = FootpathSlopeType.FLAT
                z = base_z + LAND_HEIGHT_STEP
            elif s_type == FootpathSlopeType.SLOPED:
                z = base_z
                s_dir = Direction(s_dir_int)
            else:
                z = base_z
                s_dir = Direction(0)

        flags = PathConstructFlags(0)
        if queue:
            flags = PathConstructFlags.IS_QUEUE
        return ActionResult.from_response(
            self._client.actions.footpath_place(
                x=tile.x * TILE_SIZE,
                y=tile.y * TILE_SIZE,
                z=z,
                object=self._resolve_surface(surface, queue=queue),
                railings_object=self._resolve_railings(railings),
                direction=INVALID_DIRECTION,
                slope_type=s_type,
                slope_direction=s_dir,
                construct_flags=flags,
            )
        )

    def remove(
        self,
        tile: Tile,
        *,
        height: int | None = None,
    ) -> ActionResult:
        """Remove a footpath.

        Args:
            tile: Which tile to remove the path from.
            height: Height in land steps. None = ground level.
        """
        z = self._client.world.resolve_height(tile, height)
        return ActionResult.from_response(
            self._client.actions.footpath_remove(
                x=tile.x * TILE_SIZE,
                y=tile.y * TILE_SIZE,
                z=z,
            )
        )

    def place_addition(
        self,
        tile: Tile,
        addition: FootpathAdditionInfo,
        *,
        height: int | None = None,
    ) -> ActionResult:
        """Place a path addition (bench, lamp, bin, etc.) on an existing path.

        Args:
            tile: Tile with an existing path.
            addition: Which addition to place.
            height: Height in land steps. None = ground level.
        """
        z = self._client.world.resolve_height(tile, height)
        obj_index = _resolve_object_index(
            self._client,
            "footpath_addition",
            addition.identifier,
        )
        return ActionResult.from_response(
            self._client.actions.footpath_addition_place(
                x=tile.x * TILE_SIZE,
                y=tile.y * TILE_SIZE,
                z=z,
                object=obj_index,
            )
        )

    def remove_addition(
        self,
        tile: Tile,
        *,
        height: int | None = None,
    ) -> ActionResult:
        """Remove a path addition from an existing path.

        Args:
            tile: Tile with a path that has an addition.
            height: Height in land steps. None = ground level.
        """
        z = self._client.world.resolve_height(tile, height)
        return ActionResult.from_response(
            self._client.actions.footpath_addition_remove(
                x=tile.x * TILE_SIZE,
                y=tile.y * TILE_SIZE,
                z=z,
            )
        )
