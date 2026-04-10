"""PathsProxy — footpath placement and removal."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from pyrct2._generated.enums import (
    Direction,
    EdgeBit,
    FootpathSlopeType,
    INVALID_DIRECTION,
    PathConstructFlags,
)
from pyrct2._generated.objects import (
    FootpathAdditionInfo,
    FootpathRailingsInfo,
    FootpathSurfaceInfo,
)
from pyrct2.errors import ActionError
from pyrct2.result import ActionResult
from pyrct2.world._slope import LAND_HEIGHT_STEP
from pyrct2.world._tile import TILE_SIZE, Tile


@dataclass(frozen=True)
class LineResult:
    """Result of placing a line of paths.

    ``results`` contains one entry per tile in order. Each entry is either
    an :class:`ActionResult` (success) or an :class:`ActionError` (failure).
    Failed tiles do not stop placement — all tiles are attempted.
    """

    results: list[ActionResult | ActionError] = field(default_factory=list)

    @property
    def succeeded(self) -> int:
        """Number of tiles placed successfully."""
        return sum(1 for r in self.results if isinstance(r, ActionResult))

    @property
    def failed(self) -> int:
        """Number of tiles that failed."""
        return sum(1 for r in self.results if isinstance(r, ActionError))

    @property
    def total_cost(self) -> int:
        """Sum of costs for successful placements."""
        return sum(r.cost for r in self.results if isinstance(r, ActionResult))


if TYPE_CHECKING:
    from pyrct2._generated.state import FootpathElement
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


# Edge traversal: (edge_bit, dx, dy, opposite_edge_bit).
_EDGE_NEIGHBORS: list[tuple[int, int, int, int]] = [
    (EdgeBit.WEST, -1, 0, EdgeBit.EAST),
    (EdgeBit.SOUTH, 0, 1, EdgeBit.NORTH),
    (EdgeBit.EAST, 1, 0, EdgeBit.WEST),
    (EdgeBit.NORTH, 0, -1, EdgeBit.SOUTH),
]

# Direction → EdgeBit for determining slope high-end edge.
_DIR_TO_EDGE: dict[int, int] = {
    Direction.WEST: EdgeBit.WEST,
    Direction.NORTH: EdgeBit.NORTH,
    Direction.EAST: EdgeBit.EAST,
    Direction.SOUTH: EdgeBit.SOUTH,
}


def _edge_z(path: FootpathElement, edge_bit: int) -> int:
    """Z-height at a specific edge of a path element.

    Flat paths connect at baseZ on all edges. Sloped paths connect at
    baseZ on the low end and baseZ + LAND_HEIGHT_STEP on the high end.
    """
    if path.slopeDirection is None:
        return path.baseZ
    high_edge = _DIR_TO_EDGE[int(path.slopeDirection)]
    if edge_bit == high_edge:
        return path.baseZ + LAND_HEIGHT_STEP
    return path.baseZ


def _path_reachable_at(path: FootpathElement, z: int) -> bool:
    """Whether a path element can be reached at z-height."""
    if path.slopeDirection is None:
        return z == path.baseZ
    return z == path.baseZ or z == path.baseZ + LAND_HEIGHT_STEP


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

    def place_line(
        self,
        from_tile: Tile,
        to_tile: Tile,
        *,
        queue: bool = False,
        surface: FootpathSurfaceInfo | None = None,
        railings: FootpathRailingsInfo | None = None,
    ) -> LineResult:
        """Place paths in a straight cardinal line (best-effort).

        Places a path on every tile from ``from_tile`` to ``to_tile``
        inclusive. The line must be horizontal or vertical (same x or same y).
        Each tile uses terrain-aware auto-placement.

        Obstacles don't stop placement — every tile is attempted. Check
        :attr:`LineResult.failed` and inspect individual results for errors.

        Args:
            from_tile: Starting tile.
            to_tile: Ending tile (inclusive).
            queue: If True, place queue paths.
            surface: Footpath surface. None = scenario default.
            railings: Footpath railings. None = scenario default.

        Raises:
            ValueError: If the line is not cardinal (diagonal).
        """
        dx = to_tile.x - from_tile.x
        dy = to_tile.y - from_tile.y
        if dx != 0 and dy != 0:
            raise ValueError(f"place_line requires a cardinal line (same x or same y), got {from_tile} → {to_tile}")

        # Build tile list
        if dx != 0:
            step = 1 if dx > 0 else -1
            tiles = [Tile(x, from_tile.y) for x in range(from_tile.x, to_tile.x + step, step)]
        elif dy != 0:
            step = 1 if dy > 0 else -1
            tiles = [Tile(from_tile.x, y) for y in range(from_tile.y, to_tile.y + step, step)]
        else:
            tiles = [from_tile]

        results: list[ActionResult | ActionError] = []
        for tile in tiles:
            try:
                r = self.place(tile, queue=queue, surface=surface, railings=railings)
                results.append(r)
            except ActionError as e:
                results.append(e)

        return LineResult(results=results)

    def is_connected(
        self,
        from_tile: Tile,
        to_tile: Tile,
        *,
        from_height: int | None = None,
        to_height: int | None = None,
    ) -> bool:
        """Check if paths at two tiles are connected by walking edges.

        BFS over path edge bitmasks, respecting z-levels. Paths at
        different heights are not connected unless linked by slopes.
        Returns False if either tile has no path.

        Args:
            from_tile: Starting tile.
            to_tile: Destination tile.
            from_height: Height in land steps at the starting tile.
                Required if the tile has multiple paths (stacked).
            to_height: Height in land steps at the destination tile.
                Required if the tile has multiple paths (stacked).

        Raises:
            ValueError: If a tile has multiple paths and the corresponding
                height is not specified.
        """
        from collections import deque

        all_paths = self._client.world.get_paths()

        from_paths = all_paths.get((from_tile.x, from_tile.y), [])
        to_paths = all_paths.get((to_tile.x, to_tile.y), [])
        if not from_paths or not to_paths:
            return False

        if len(from_paths) > 1 and from_height is None:
            raise ValueError(
                f"{from_tile} has {len(from_paths)} paths at different heights — specify from_height to disambiguate"
            )
        if len(to_paths) > 1 and to_height is None:
            raise ValueError(
                f"{to_tile} has {len(to_paths)} paths at different heights — specify to_height to disambiguate"
            )

        # Filter to the specified path when height is given
        if from_height is not None:
            from_z = from_height * LAND_HEIGHT_STEP
            from_paths = [p for p in from_paths if _path_reachable_at(p, from_z)]
            if not from_paths:
                return False
        if to_height is not None:
            to_z = to_height * LAND_HEIGHT_STEP
            to_paths = [p for p in to_paths if _path_reachable_at(p, to_z)]
            if not to_paths:
                return False

        # Trivial: same tile, same path
        if from_tile == to_tile:
            return True

        # Target z-values
        target_zs: set[int] = set()
        for p in to_paths:
            target_zs.add(p.baseZ)
            if p.slopeDirection is not None:
                target_zs.add(p.baseZ + LAND_HEIGHT_STEP)

        # Seed BFS from paths at from_tile
        start: set[tuple[int, int, int]] = set()
        for p in from_paths:
            start.add((from_tile.x, from_tile.y, p.baseZ))
            if p.slopeDirection is not None:
                start.add((from_tile.x, from_tile.y, p.baseZ + LAND_HEIGHT_STEP))

        visited: set[tuple[int, int, int]] = set(start)
        queue: deque[tuple[int, int, int]] = deque(start)

        while queue:
            x, y, z = queue.popleft()

            for path_elem in all_paths.get((x, y), []):
                if not _path_reachable_at(path_elem, z):
                    continue
                for edge_bit, dx, dy, _opp in _EDGE_NEIGHBORS:
                    if not (path_elem.edges & edge_bit):
                        continue
                    nz = _edge_z(path_elem, edge_bit)
                    nx, ny = x + dx, y + dy
                    node = (nx, ny, nz)
                    if nx == to_tile.x and ny == to_tile.y and nz in target_zs:
                        return True
                    if node not in visited:
                        visited.add(node)
                        queue.append(node)

        return False

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
