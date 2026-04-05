"""RidesProxy and RideEntity — ride queries, placement, and management."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from pyrct2._generated.enums import (
    Direction,
    RideInspection,
    RideStatus,
    RideType,
    SelectedLiftAndInverted,
    TrackElemType,
)
from pyrct2._generated.objects import RIDE_TYPE_TRACK_ELEMS, RideObjectInfo
from pyrct2._generated.state import Ride
from pyrct2.result import ActionResult
from pyrct2.world._slope import LAND_HEIGHT_STEP
from pyrct2.world._tile import TILE_SIZE, Tile

if TYPE_CHECKING:
    from pyrct2.client import RCT2


class StationAccess(BaseModel):
    """A station entrance or exit: tile position + facing direction."""

    model_config = ConfigDict(frozen=True)

    tile: Tile
    direction: Direction


class RideEntity:
    """Wrapper around a Ride snapshot that adds action methods.

    All properties are accessible via ``.data`` (the Pydantic model snapshot).
    Action methods send game commands via the client.
    """

    def __init__(self, client: RCT2, model: Ride) -> None:
        self._client = client
        self.data = model

    def __repr__(self) -> str:
        return f"RideEntity(#{self.data.id} {self.data.name!r} {self.data.status})"

    @property
    def _id(self) -> int:
        return self.data.id

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


class RidesProxy:
    """Ride queries, placement, and management: ``game.rides``."""

    def __init__(self, client: RCT2) -> None:
        self._client = client

    # -- Query methods --

    def get(self, ride_id: int) -> RideEntity | None:
        """Get a specific ride by ID, or None if not found."""
        for r in self._client.state.rides():
            if r.id == ride_id:
                return RideEntity(self._client, r)
        return None

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
    ) -> int:
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
            The ride ID (int) for use with open(), demolish(), etc.

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
        ride_id, ride_type = self._create_ride(obj, tile, height, direction)

        # TODO: Add rollback/transaction support. If entrance/exit placement
        # fails after ride_create, the ride slot is orphaned. A general
        # transaction pattern (context manager?) would auto-demolish on failure.
        # For now, failures leave an orphaned ride that the developer must clean up.

        # Place entrance and exit
        self._client.actions.ride_entrance_exit_place(
            x=entrance.x * TILE_SIZE,
            y=entrance.y * TILE_SIZE,
            direction=direction,
            ride=ride_id,
            station=0,
            is_exit=False,
        )
        self._client.actions.ride_entrance_exit_place(
            x=exit.x * TILE_SIZE,
            y=exit.y * TILE_SIZE,
            direction=direction,
            ride=ride_id,
            station=0,
            is_exit=True,
        )

        return ride_id

    def place_stall(
        self,
        obj: RideObjectInfo,
        tile: Tile,
        height: int | None = None,
        direction: Direction = Direction.NORTH,
    ) -> int:
        """Place a stall (shop, food stand, restroom, etc.).

        Stalls are 1x1 rides that don't need entrance or exit. The direction
        controls which way the stall faces (where guests approach from).

        Args:
            obj: A stall object (e.g. RideObjects.stall.BURGER_BAR).
            tile: The tile to place the stall on.
            height: Height in land steps. Defaults to surface height.
            direction: Facing direction. Defaults to NORTH.

        Returns:
            The ride ID (int) for use with open(), demolish(), etc.

        Raises:
            ValueError: If the object is not a stall, or height is below surface.
            RuntimeError: If the stall object is not loaded in the scenario.
            ActionError: If placement fails (terrain, clearance, ownership, etc.).
        """
        _require_stall(obj)
        ride_id, _ = self._create_ride(obj, tile, height, direction)
        return ride_id

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

        z = _resolve_height(self._client, tile, height)

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

    def open(self, ride_id: int) -> ActionResult:
        """Open a ride for guests."""
        return ActionResult.from_response(
            self._client.actions.ride_set_status(
                ride=ride_id,
                status=RideStatus.OPEN,
            )
        )

    def close(self, ride_id: int) -> ActionResult:
        """Close a ride."""
        return ActionResult.from_response(
            self._client.actions.ride_set_status(
                ride=ride_id,
                status=RideStatus.CLOSED,
            )
        )

    def demolish(self, ride_id: int) -> ActionResult:
        """Demolish a ride, removing it from the map."""
        from pyrct2._generated.enums import RideModifyType

        return ActionResult.from_response(
            self._client.actions.ride_demolish(
                ride=ride_id,
                modify_type=RideModifyType.DEMOLISH,
            )
        )

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


def _resolve_height(client: RCT2, tile: Tile, height: int | None) -> int:
    """Return world-unit Z for the given height, or surface height if None."""
    surface_z = client.world.get_tile(tile).surface.baseZ
    if height is not None:
        z = height * LAND_HEIGHT_STEP
        if z < surface_z:
            raise ValueError(
                f"Height {height} land steps (z={z}) is below the surface at "
                f"tile ({tile.x}, {tile.y}) which is at {surface_z // LAND_HEIGHT_STEP} "
                f"land steps (z={surface_z}). Raise the land first or use a higher value."
            )
        return z
    return surface_z


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
