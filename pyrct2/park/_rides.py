"""RidesProxy and RideEntity — ride queries, placement, and management."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from pyrct2._generated.enums import (
    Direction,
    EdgeBit,
    RideInspection,
    RideModifyType,
    RideSetSetting,
    RideStatus,
    RideType,
    SelectedLiftAndInverted,
    TrackElemType,
)
from pyrct2._entity import EntityBase
from pyrct2._generated.objects import RIDE_TYPE_TRACK_ELEMS, RideObjectInfo
from pyrct2._generated.state import Ride
from pyrct2.errors import ActionError, QueryError
from pyrct2.result import ActionResult
from pyrct2.world._tile import DIR_DELTA, TILE_SIZE, Tile

if TYPE_CHECKING:
    from pyrct2.client import RCT2

# Direction → EdgeBit. The edge a path needs to connect in that direction.
_DIR_EDGE = {
    Direction.WEST: EdgeBit.WEST,
    Direction.NORTH: EdgeBit.NORTH,
    Direction.EAST: EdgeBit.EAST,
    Direction.SOUTH: EdgeBit.SOUTH,
}


class StationAccess(BaseModel):
    """A station entrance or exit: tile position + facing direction.

    TODO: ``direction`` reports the ride's orientation, not the entrance/exit's
    true facing. Both entrance and exit return the same direction regardless of
    placement. Do not rely on it for path connectivity — use
    ``RideEntity.is_entrance_connected()`` instead.
    """

    model_config = ConfigDict(frozen=True)

    tile: Tile
    direction: Direction


def _access_path_tile(access: StationAccess, client: RCT2, ride_id: int) -> tuple[Tile, EdgeBit]:
    """The tile where a path must exist to connect to this entrance/exit.

    Returns (path_tile, required_edge). The path on path_tile must have
    required_edge set to actually connect to the entrance/exit.

    The entrance/exit direction field is unreliable (reports ride direction,
    not true facing). Instead, find the neighbor with track belonging to
    this ride, then the path tile is on the opposite side.
    """
    for d, (dx, dy) in DIR_DELTA.items():
        neighbor = Tile(access.tile.x + dx, access.tile.y + dy)
        td = client.world.get_tile(neighbor)
        if any(t.ride == ride_id for t in td.tracks):
            # Path is on the opposite side from the ride
            opposite = Direction((d + 2) % 4)
            odx, ody = DIR_DELTA[opposite]
            path_tile = Tile(access.tile.x + odx, access.tile.y + ody)
            # Path needs an edge pointing back toward the entrance
            required_edge = _DIR_EDGE[d]
            return path_tile, required_edge
    return access.tile, EdgeBit(0)


def _entrance_direction(access_tile: Tile, footprint: set[Tile], ride_direction: Direction) -> Direction:
    """Compute the correct direction for ride_entrance_exit_place.

    Empirically determined by placing entrances via the game UI on all
    4 sides of a NORTH-facing ride and reading the resulting direction:

        Position    Toward-ride    Game UI dir
        North       S(3)           N(1)  ← opposite
        South       N(1)           S(3)  ← opposite
        East        W(0)           W(0)  ← same
        West        E(2)           E(2)  ← same

    Rule: if toward-ride is odd (N=1 or S=3), use opposite.
          If toward-ride is even (W=0 or E=2), use same.
    """
    for d, (dx, dy) in DIR_DELTA.items():
        neighbor = Tile(access_tile.x + dx, access_tile.y + dy)
        if neighbor in footprint:
            # d = direction from entrance toward ride
            if d % 2 == 1:  # N or S: use opposite
                return Direction((d + 2) % 4)
            else:  # W or E: use same
                return d
    raise ValueError(f"Tile ({access_tile.x}, {access_tile.y}) is not adjacent to the footprint")


class RideEntity(EntityBase):
    """Wrapper around a Ride snapshot that adds action methods.

    All properties are accessible via ``.data`` (the Pydantic model snapshot).
    Rides are not peeps — they don't have world position or move_to.
    """

    def __repr__(self) -> str:
        return f"RideEntity(#{self.data.id} {self.data.name!r} {self.data.status})"

    # -- Read helpers --

    @property
    def placement_tile(self) -> Tile:
        """Placement origin tile (the tile passed to place_flat_ride/place_stall).

        For 1x1 stalls this is the only tile. For larger rides, use get_footprint()
        with this origin to compute all occupied tiles.
        """
        s = self.data.stations[0].start
        assert s is not None, f"Ride #{self.data.id} has no station start"
        return Tile.from_world(s.x, s.y)

    @property
    def direction(self) -> Direction | None:
        """Facing direction for stalls, None for rides.

        Stalls face a specific direction (where guests approach from).
        Rides don't have a meaningful facing — use entrance.direction / exit.direction instead.
        Requires a tile lookup for stalls (one round-trip).
        """
        if self.data.stations[0].entrance is not None:
            return None
        td = self._client.world.get_tile(self.placement_tile)
        track = next(t for t in td.tracks if t.ride == self._id)
        return Direction(track.direction)

    @property
    def entrance(self) -> StationAccess | None:
        """First station's entrance, or None for stalls.

        TODO: direction is the ride's orientation, not the entrance's true facing.
        Both entrance and exit report the same direction regardless of placement.
        True facing can be derived from the access tile's position relative to
        the ride footprint (check which cardinal neighbor has a track element).
        """
        e = self.data.stations[0].entrance
        if e is None:
            return None
        return StationAccess(
            tile=Tile.from_world(e.x, e.y),
            direction=Direction(e.direction),
        )

    @property
    def exit(self) -> StationAccess | None:
        """First station's exit, or None for stalls.

        TODO: direction is the ride's orientation, not the exit's true facing.
        See entrance property for details.
        """
        e = self.data.stations[0].exit
        if e is None:
            return None
        return StationAccess(
            tile=Tile.from_world(e.x, e.y),
            direction=Direction(e.direction),
        )

    def is_reachable(self, target: Tile | None = None) -> bool:
        """Check if guests can reach this ride or stall.

        For rides: checks both entrance and exit have an adjacent path
        with an edge facing the entrance/exit.
        For stalls: checks the tile the stall faces has a path with an
        edge facing the stall.

        If ``target`` is given, also verifies path connectivity to that
        tile (e.g. the park entrance). Expensive with target (BFS over
        all paths).

        For diagnostics on which part is disconnected, check
        ``is_entrance_reachable`` / ``is_exit_reachable`` individually.
        """
        if self.entrance is not None:
            return self.is_entrance_reachable(target) and self.is_exit_reachable(target)
        return self._check_path(*self._stall_path_info(), target)

    def is_entrance_reachable(self, target: Tile | None = None) -> bool:
        """Check if the ride entrance has a connected path with correct edge.

        Returns False for stalls (no entrance).
        """
        info = self._ride_path_info(self.entrance)
        if info is None:
            return False
        return self._check_path(*info, target)

    def is_exit_reachable(self, target: Tile | None = None) -> bool:
        """Check if the ride exit has an adjacent path.

        Unlike entrances, exits don't require a specific edge — the game
        engine connects guests to any adjacent path regardless of edges.

        Returns False for stalls (no exit).
        """
        info = self._ride_path_info(self.exit)
        if info is None:
            return False
        tile, _edge = info
        return self._check_path(tile, EdgeBit(0), target)

    def _check_path(self, tile: Tile | None, required_edge: EdgeBit, target: Tile | None) -> bool:
        if tile is None:
            return False
        td = self._client.world.get_tile(tile)
        if not td.paths:
            return False
        # Edge check: a path/queue with 2+ edges (connected on both sides)
        # but none facing the entrance is fenced off — the perpendicular
        # queue problem. Paths with 0 or 1 edges connect to the entrance
        # implicitly via the game engine (edges are never set toward
        # entrance/exit elements).
        if required_edge:
            for p in td.paths:
                edge_count = bin(p.edges).count("1")
                if edge_count >= 2 and not (p.edges & required_edge):
                    return False
        if target is None:
            return True
        return self._client.paths.is_connected(tile, target)

    def _ride_path_info(self, access: StationAccess | None) -> tuple[Tile, EdgeBit] | None:
        """Find the path tile + required edge for a ride entrance/exit."""
        if access is None:
            return None
        return _access_path_tile(access, self._client, self._id)

    def _stall_path_info(self) -> tuple[Tile | None, EdgeBit]:
        """Find the path tile + required edge for a stall."""
        d = self.direction
        if d is None:
            return None, EdgeBit(0)
        dx, dy = DIR_DELTA[d]
        tile = Tile(self.placement_tile.x + dx, self.placement_tile.y + dy)
        opposite = Direction((d + 2) % 4)
        return tile, _DIR_EDGE[opposite]

    def refresh(self) -> None:
        """Re-fetch this ride's state from the game.

        Warning: ride IDs are reused. If this ride was demolished and a new
        ride received the same ID, this will silently load the wrong data.
        """
        ride_data = self._client._query("rides", {"id": self._id})
        self.data = Ride.model_validate(ride_data)

    # -- Write methods --

    def rename(self, name: str) -> ActionResult:
        """Rename the ride/stall."""
        return ActionResult.from_response(
            self._client.actions.ride_set_name(
                ride=self._id,
                name=name,
            )
        )

    def set_price(self, price: int) -> ActionResult:
        """Set the ride/stall entry price."""
        return ActionResult.from_response(
            self._client.actions.ride_set_price(
                ride=self._id,
                price=price,
                is_primary_price=True,
            )
        )

    def open(self) -> ActionResult:
        """Open the ride/stall for guests."""
        return ActionResult.from_response(
            self._client.actions.ride_set_status(
                ride=self._id,
                status=RideStatus.OPEN,
            )
        )

    def close(self) -> ActionResult:
        """Close the ride/stall."""
        return ActionResult.from_response(
            self._client.actions.ride_set_status(
                ride=self._id,
                status=RideStatus.CLOSED,
            )
        )

    def demolish(self) -> ActionResult:
        """Demolish the ride/stall, removing it from the map."""
        return ActionResult.from_response(
            self._client.actions.ride_demolish(
                ride=self._id,
                modify_type=RideModifyType.DEMOLISH,
            )
        )

    def set_min_wait_time(self, seconds: int) -> ActionResult:
        """Set minimum wait time before dispatch (seconds)."""
        return ActionResult.from_response(
            self._client.actions.ride_set_setting(
                ride=self._id,
                setting=RideSetSetting.MIN_WAITING_TIME,
                value=seconds,
            )
        )

    def set_max_wait_time(self, seconds: int) -> ActionResult:
        """Set maximum wait time before dispatch (seconds)."""
        return ActionResult.from_response(
            self._client.actions.ride_set_setting(
                ride=self._id,
                setting=RideSetSetting.MAX_WAITING_TIME,
                value=seconds,
            )
        )

    def set_inspection_interval(self, interval: RideInspection) -> ActionResult:
        """Set how often mechanics inspect this ride."""
        return ActionResult.from_response(
            self._client.actions.ride_set_setting(
                ride=self._id,
                setting=RideSetSetting.INSPECTION_INTERVAL,
                value=interval,
            )
        )


class RidesProxy:
    """Ride queries, placement, and management: ``game.rides``."""

    def __init__(self, client: RCT2) -> None:
        self._client = client

    # -- Query methods --

    def get(self, ride_id: int) -> RideEntity | None:
        """Get a specific ride by ID, or None if not found."""
        try:
            ride_data = self._client._query("rides", {"id": ride_id})
        except QueryError as e:
            if e.error == "not_found":
                return None
            raise
        ride = Ride.model_validate(ride_data)
        return RideEntity(self._client, ride)

    def get_footprint(
        self,
        obj: RideObjectInfo,
        tile: Tile,
        direction: Direction = Direction.NORTH,
    ) -> list[Tile]:
        """Return the tiles a flat ride will occupy when placed.

        The meaning of ``tile`` depends on the ride's footprint size:

        - **Odd square** (1x1, 3x3): ``tile`` is the center.
        - **Even square** (2x2, 4x4): ``tile`` is a corner; which corner
          depends on ``direction``.
        - **Odd rectangle** (1x5): ``tile`` is the center; the strip runs
          horizontally for WEST/EAST, vertically for NORTH/SOUTH.
        - **Even rectangle** (1x4): asymmetric; offsets are direction-specific
          (empirically measured).

        Args:
            obj: The ride object (must have tiles_x and tiles_y).
            tile: The placement tile (passed to track_place).
            direction: Facing direction. Defaults to NORTH.

        Returns:
            List of all tiles the ride footprint will occupy.
        """
        return _compute_footprint(obj, tile, direction)

    def place_flat_ride(
        self,
        obj: RideObjectInfo,
        tile: Tile,
        entrance: Tile,
        exit: Tile,
        height: int | None = None,
        direction: Direction = Direction.NORTH,
    ) -> RideEntity:
        """Place a flat ride or stall with entrance and exit.

        The meaning of ``tile`` depends on the ride's footprint size — see
        :meth:`get_footprint` for details. For odd-square rides like a
        Merry-Go-Round (3x3), the tile is the center. For even-square rides
        like Bumper Cars (4x4), the tile is a corner that rotates with direction.

        Entrance and exit must be adjacent to the footprint edge but **not**
        inside it. For stalls (1x1, no entrance/exit), use :meth:`place_stall`.

        Args:
            obj: The ride object to place (e.g. RideObjects.gentle.MERRY_GO_ROUND).
            tile: The placement tile (see get_footprint for semantics).
            entrance: The tile for the entrance (must be adjacent to footprint).
            exit: The tile for the exit (must be adjacent to footprint).
            height: Height in land steps. Defaults to the surface height of the tile.
            direction: Facing direction of the ride. Defaults to NORTH.

        Returns:
            The placed ride as a :class:`RideEntity`.

        Raises:
            RuntimeError: If the ride object is not loaded in the scenario.
            ValueError: If height is below the surface, entrance/exit is inside
                or not adjacent to the footprint, or no track type found.
            ActionError: If placement fails (terrain, clearance, ownership, etc.).
        """
        # Step 0: Validate entrance/exit against footprint
        footprint = _compute_footprint(obj, tile, direction)
        footprint_set = set(footprint)
        adjacent = _adjacent_tiles(footprint_set)

        if entrance in footprint_set:
            raise ValueError(
                f"Entrance {entrance} is inside the ride footprint. "
                f"Place it on a tile adjacent to the footprint edge, not on top of it."
            )
        if entrance not in adjacent:
            raise ValueError(
                f"Entrance {entrance} is not adjacent to the ride footprint. "
                f"Place it on a tile directly next to (not diagonal to) the footprint edge."
            )
        if exit in footprint_set:
            raise ValueError(
                f"Exit {exit} is inside the ride footprint. "
                f"Place it on a tile adjacent to the footprint edge, not on top of it."
            )
        if exit not in adjacent:
            raise ValueError(
                f"Exit {exit} is not adjacent to the ride footprint. "
                f"Place it on a tile directly next to (not diagonal to) the footprint edge."
            )
        # Pre-check: entrance/exit tiles must have only a surface element
        for label, t in [("Entrance", entrance), ("Exit", exit)]:
            td = self._client.world.get_tile(t)
            blockers = [e.type for e in td.elements if e.type != "surface"]
            if blockers:
                raise ValueError(
                    f"{label} tile ({t.x}, {t.y}) is blocked by: {', '.join(blockers)}. "
                    f"Clear the tile or choose a different one."
                )

        ride_id, ride_type = self._create_ride(obj, tile, height, direction)

        # Compute entrance/exit direction: must face TOWARD the ride
        # (the open/guest side faces the opposite way automatically).
        entrance_dir = _entrance_direction(entrance, footprint_set, direction)
        exit_dir = _entrance_direction(exit, footprint_set, direction)

        # Place entrance and exit, rolling back the ride on failure
        try:
            self._client.actions.ride_entrance_exit_place(
                x=entrance.x * TILE_SIZE,
                y=entrance.y * TILE_SIZE,
                direction=entrance_dir,
                ride=ride_id,
                station=0,
                is_exit=False,
            )
            self._client.actions.ride_entrance_exit_place(
                x=exit.x * TILE_SIZE,
                y=exit.y * TILE_SIZE,
                direction=exit_dir,
                ride=ride_id,
                station=0,
                is_exit=True,
            )
        except ActionError:
            # Demolish the orphaned ride so it doesn't pollute the game
            self._client.actions.ride_demolish(
                ride=ride_id,
                modify_type=RideModifyType.DEMOLISH,
            )
            raise

        ride = self.get(ride_id)
        if ride is None:
            raise RuntimeError(f"Placed ride (id={ride_id}) not found after creation")
        return ride

    def place_stall(
        self,
        obj: RideObjectInfo,
        tile: Tile,
        height: int | None = None,
        direction: Direction = Direction.NORTH,
    ) -> RideEntity:
        """Place a stall (shop, food stand, restroom, etc.).

        Stalls are 1x1 rides that don't need entrance or exit. The direction
        controls which way the stall faces (where guests approach from).

        Args:
            obj: A stall object (e.g. RideObjects.stall.BURGER_BAR).
            tile: The tile to place the stall on.
            height: Height in land steps. Defaults to surface height.
            direction: Facing direction. Defaults to NORTH.

        Returns:
            The placed stall as a :class:`RideEntity`.

        Raises:
            ValueError: If the object is not a stall, or height is below surface.
            RuntimeError: If the stall object is not loaded in the scenario.
            ActionError: If placement fails (terrain, clearance, ownership, etc.).
        """
        _require_stall(obj)
        ride_id, _ = self._create_ride(obj, tile, height, direction)
        ride = self.get(ride_id)
        if ride is None:
            raise RuntimeError(f"Placed stall (id={ride_id}) not found after creation")
        return ride

    def _create_ride(
        self,
        obj: RideObjectInfo,
        tile: Tile,
        height: int | None,
        direction: Direction,
    ) -> tuple[int, RideType]:
        """Shared flow: resolve object → create ride slot → resolve height → place track.

        Returns (ride_id, ride_type).
        """
        obj_index = self._client.objects._require_loaded_index(obj)
        ride_type = _resolve_ride_type(obj)
        track_type = _resolve_track_type(obj)

        # TODO: Action results are untyped dicts. Codegen should generate typed
        # response models from the d.ts *ActionResult interfaces (e.g.
        # RideCreateActionResult with .ride, TrackPlaceActionResult with .position).
        result = self._client.actions.ride_create(
            ride_type=ride_type,
            ride_object=obj_index,
            entrance_object=0,
            colour1=0,
            colour2=0,
            inspection_interval=RideInspection.EVERY30_MINUTES,
        )
        ride_id = result["payload"]["ride"]

        z = self._client.world.resolve_height(tile, height)

        self._client.actions.track_place(
            x=tile.x * TILE_SIZE,
            y=tile.y * TILE_SIZE,
            z=z,
            direction=direction,
            ride=ride_id,
            track_type=track_type,
            ride_type=ride_type,
            brake_speed=0,
            colour=0,
            seat_rotation=4,
            track_place_flags=SelectedLiftAndInverted(0),
            is_from_track_design=False,
        )

        return ride_id, ride_type

    def list(self) -> list[RideEntity]:
        """Return all rides as entity wrappers."""
        return [RideEntity(self._client, r) for r in self._client.state.rides()]


# ── Helpers ───────────────────────────────────────────────────────────


def _adjacent_tiles(footprint: set[Tile]) -> set[Tile]:
    """Return tiles cardinally adjacent to the footprint but not inside it."""
    adjacent = set()
    for t in footprint:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            neighbor = Tile(t.x + dx, t.y + dy)
            if neighbor not in footprint:
                adjacent.add(neighbor)
    return adjacent


def _compute_footprint(obj: RideObjectInfo, tile: Tile, direction: Direction) -> list[Tile]:
    """Compute the tiles occupied by a flat ride.

    Algorithm derived from empirical probing of all 6 footprint sizes across all 4 directions.
    """
    tx, ty = obj.tiles_x, obj.tiles_y
    if tx is None or ty is None:
        raise ValueError(f"'{obj.name}' ({obj.identifier}) has no footprint dimensions (tiles_x/tiles_y).")

    # 1x1: trivial
    if tx == 1 and ty == 1:
        return [tile]

    # Odd square (3x3, etc.): centered on placement tile, direction ignored
    if tx == ty and tx % 2 == 1:
        half = (tx - 1) // 2
        return [Tile(tile.x + dx, tile.y + dy) for dx in range(-half, half + 1) for dy in range(-half, half + 1)]

    # Even square (2x2, 4x4): placement tile is a corner, block rotates with direction
    if tx == ty and tx % 2 == 0:
        n = tx
        offsets = {
            Direction.WEST: (0, 0),
            Direction.NORTH: (0, -(n - 1)),
            Direction.EAST: (-(n - 1), -(n - 1)),
            Direction.SOUTH: (-(n - 1), 0),
        }
        ox, oy = offsets[direction]
        return [Tile(tile.x + ox + i, tile.y + oy + j) for i in range(n) for j in range(n)]

    # Rectangular rides
    length = max(tx, ty)

    # Odd-length rectangle (1x5): centered, flips orientation with direction
    if length % 2 == 1:
        half = (length - 1) // 2
        if direction in (Direction.WEST, Direction.EAST):
            return [Tile(tile.x + dx, tile.y) for dx in range(-half, half + 1)]
        return [Tile(tile.x, tile.y + dy) for dy in range(-half, half + 1)]

    # Even-length rectangle (1x4): asymmetric, empirically measured per direction
    # Measured for FLAT_TRACK1X4_C (Ferris Wheel). Other even-length rectangular
    # track types may differ — see research doc caveat.
    if direction == Direction.WEST:
        return [Tile(tile.x + dx, tile.y) for dx in (-2, -1, 0, 1)]
    if direction == Direction.NORTH:
        return [Tile(tile.x, tile.y + dy) for dy in (-1, 0, 1, 2)]
    if direction == Direction.EAST:
        return [Tile(tile.x + dx, tile.y) for dx in (-1, 0, 1, 2)]
    # SOUTH
    return [Tile(tile.x, tile.y + dy) for dy in (-2, -1, 0, 1)]


def _require_stall(obj: RideObjectInfo) -> None:
    """Raise ValueError if the object is not a stall."""
    category = obj.category if isinstance(obj.category, str) else obj.category[0] if obj.category else ""
    if category != "stall":
        raise ValueError(
            f"'{obj.name}' ({obj.identifier}) is not a stall (category='{obj.category}'). "
            f"Use place_flat_ride() for non-stall rides."
        )


def _resolve_ride_type(obj: RideObjectInfo) -> RideType:
    """Convert a ride object's type string to the RideType enum."""
    type_str = obj.ride_type.upper()
    try:
        return RideType[type_str]
    except KeyError:
        raise ValueError(
            f"Unknown ride type '{obj.ride_type}' for object {obj.identifier}. "
            f"This object may not be supported by the current RideType enum."
        ) from None


def _resolve_track_type(obj: RideObjectInfo) -> TrackElemType:
    """Resolve the correct TrackElemType for a flat ride object.

    Uses the generated RIDE_TYPE_TRACK_ELEMS mapping to find the
    correct flat track type (e.g. FLAT_TRACK3X3 = 266 for Merry-Go-Round).

    Raises ValueError if the ride type is not a flat ride.
    """
    track_value = RIDE_TYPE_TRACK_ELEMS.get(obj.ride_type)
    if track_value is None:
        raise ValueError(
            f"'{obj.name}' (ride type '{obj.ride_type}') is not a flat ride. "
            f"Use place_flat_ride() only for flat rides and stalls."
        )
    return TrackElemType(track_value)
