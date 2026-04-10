"""PathsProxy — footpath placement."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyrct2._generated.enums import (
    FootpathSlopeType,
    INVALID_DIRECTION,
    PathConstructFlags,
)
from pyrct2._generated.objects import FootpathRailingsInfo, FootpathSurfaceInfo
from pyrct2.result import ActionResult
from pyrct2.world._tile import TILE_SIZE, Tile

if TYPE_CHECKING:
    from pyrct2.client import RCT2


def _resolve_footpath_index(
    client: RCT2, obj_type: str, identifier: str
) -> int:
    """Resolve a footpath object identifier to its loaded slot index."""
    objects = client._query("get_objects", {"type": obj_type})
    for o in objects:
        if o["identifier"] == identifier:
            return o["index"]
    raise RuntimeError(
        f"{identifier} is not loaded in this scenario. "
        f"Loaded {obj_type}: {[o['identifier'] for o in objects]}"
    )


def _first_surface_index(client: RCT2) -> int:
    """Return the index of the first non-queue footpath surface in the scenario."""
    surfaces = client._query("get_objects", {"type": "footpath_surface"})
    for s in surfaces:
        if "queue" not in s["identifier"]:
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
        self._default_railings = _first_railings_index(client)

    def _resolve_surface(self, surface: FootpathSurfaceInfo | None) -> int:
        if surface is None:
            return self._default_surface
        return _resolve_footpath_index(
            self._client, "footpath_surface", surface.identifier,
        )

    def _resolve_railings(self, railings: FootpathRailingsInfo | None) -> int:
        if railings is None:
            return self._default_railings
        return _resolve_footpath_index(
            self._client, "footpath_railings", railings.identifier,
        )

    def place(
        self,
        tile: Tile,
        *,
        height: int | None = None,
        queue: bool = False,
        surface: FootpathSurfaceInfo | None = None,
        railings: FootpathRailingsInfo | None = None,
    ) -> ActionResult:
        """Place a footpath with auto-connect.

        Args:
            tile: Where to place the path.
            height: Height in land steps. None = ground level.
            queue: If True, place a queue path.
            surface: Footpath surface. None = scenario default.
            railings: Footpath railings. None = scenario default.
        """
        z = self._client.world.resolve_height(tile, height)
        flags = PathConstructFlags(0)
        if queue:
            flags = PathConstructFlags.IS_QUEUE
        return ActionResult.from_response(
            self._client.actions.footpath_place(
                x=tile.x * TILE_SIZE,
                y=tile.y * TILE_SIZE,
                z=z,
                object=self._resolve_surface(surface),
                railings_object=self._resolve_railings(railings),
                direction=INVALID_DIRECTION,
                slope_type=FootpathSlopeType.FLAT,
                slope_direction=0,
                construct_flags=flags,
            )
        )
