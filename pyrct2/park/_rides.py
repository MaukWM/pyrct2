"""RidesProxy, RideEntity, and TrackedRideEntity — ride queries, placement, and management."""

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
from pyrct2._generated.objects import RIDE_TYPE_STR_TO_INT, RIDE_TYPE_TRACK_ELEMS, RideObjectInfo
from pyrct2._generated.state import Ride
from pyrct2.errors import ActionError, QueryError
from pyrct2.result import (
    ActionResult,
    CursorPosition,
    PlacedPiece,
    TrackPlaceResult,
    TrackRemoveResult,
)
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

    # ── Reachability (BFS to park entrance) ──────────────────────────

    def is_entrance_reachable(self) -> bool:
        """Whether guests can walk from a park entrance to this ride's entrance.

        Checks that a connected path exists adjacent to the entrance AND
        that it connects to any park entrance via the path network.

        Returns False for stalls.
        """
        info = self._ride_path_info(self.entrance)
        if info is None:
            return False
        tile, edge = info
        if not self._has_path_at(tile, required_edge=edge):
            return False
        return self._is_connected_to_park_entrance(tile)

    def is_exit_reachable(self) -> bool:
        """Whether guests leaving can walk from this ride's exit to a park entrance.

        Checks that a path exists adjacent to the exit AND that it
        connects to any park entrance via the path network.

        Returns False for stalls.
        """
        info = self._ride_path_info(self.exit)
        if info is None:
            return False
        tile, _edge = info
        if not self._has_path_at(tile):
            return False
        return self._is_connected_to_park_entrance(tile)

    def is_stall_reachable(self) -> bool:
        """Whether this stall is reachable from a park entrance.

        Checks that the facing tile has a path AND that it connects to
        any park entrance via the path network. Unlike ride entrances,
        stalls don't require a specific path edge — the C++ shop
        connection mechanism handles stall-to-path linking internally.

        Returns False for rides (use is_entrance_reachable / is_exit_reachable).

        Known issue: stalls like Information Kiosk are accessible from all
        4 sides, but this only checks the single facing direction. A kiosk
        next to a path on any side will work in-game but may report False
        here if the facing direction doesn't point at the path.
        """
        if self.entrance is not None:
            return False
        tile, _edge = self._stall_path_info()
        if tile is None or not self._has_path_at(tile):
            return False
        return self._is_connected_to_park_entrance(tile)

    # ── Private helpers ──────────────────────────────────────────────

    def _has_path_at(self, tile: Tile | None, required_edge: EdgeBit | None = None) -> bool:
        """Check if a path exists on a tile, optionally with a required edge.

        When ``required_edge`` is None, any path on the tile is sufficient
        (used for exits, which don't require a specific edge direction).

        Note: does not consider Z-height. If stacked paths exist at
        different heights, this may match a path at the wrong level
        and produce a false positive.
        """
        if tile is None:
            return False
        td = self._client.world.get_tile(tile)
        if not td.paths:
            return False
        # Edge check: a path/queue with 2+ edges but none facing the
        # entrance is fenced off (perpendicular queue problem). Paths
        # with 0 or 1 edges connect implicitly via the game engine.
        if required_edge is not None:
            for p in td.paths:
                edge_count = bin(p.edges).count("1")
                if edge_count >= 2 and not (p.edges & required_edge):
                    return False
        return True

    def _is_connected_to_park_entrance(self, tile: Tile) -> bool:
        """BFS from tile to any park entrance arrival tile."""
        entrances = self._client.park.entrances
        return any(self._client.paths.is_connected(tile, e.arrival_tile) for e in entrances)

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
        # Stored track direction uses C++ convention where NORTH(1)=Y+
        # and SOUTH(3)=Y-. pyrct2's DIR_DELTA has the opposite for N/S.
        # Invert odd directions (same fix as _entrance_direction).
        d_visual = Direction((d + 2) % 4) if d % 2 == 1 else d
        dx, dy = DIR_DELTA[d_visual]
        tile = Tile(self.placement_tile.x + dx, self.placement_tile.y + dy)
        opposite = Direction((d_visual + 2) % 4)
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


class TrackedRideEntity(RideEntity):
    """Ride entity with track building capabilities.

    Created by ``game.rides.create_tracked_ride()``. Maintains cursor state
    so each ``.place()`` call knows where to put the next piece. The bridge
    is stateless — it returns cursor + validNext per placement, and pyrct2
    tracks the full piece history for undo support.
    """

    def __init__(
        self,
        client: RCT2,
        model: Ride,
        ride_type: RideType,
        cursor: CursorPosition,
        valid_next: list[TrackElemType],
        pieces: list[PlacedPiece],
        end_slope: int = 0,
        end_bank: int = 0,
    ) -> None:
        super().__init__(client, model)
        self._ride_type = ride_type
        self._cursor = cursor
        self._valid_next = valid_next
        self._pieces = list(pieces)
        self._end_slope = end_slope
        self._end_bank = end_bank
        self._circuit_complete = False
        # Number of station pieces (protected from undo)
        self._station_piece_count = len(pieces)
        # beginZ lookup for valid next types (populated from bridge beginZMap)
        self._begin_z_lookup: dict = {}

    def __repr__(self) -> str:
        return (
            f"TrackedRideEntity(#{self.data.id} {self.data.name!r} "
            f"pieces={len(self._pieces)} circuit={self._circuit_complete})"
        )

    # ── Track building ──────────────────────────────────────────────

    def place(
        self,
        track_type: TrackElemType,
        *,
        chain_lift: bool = False,
    ) -> TrackPlaceResult:
        """Place the next track piece at the current cursor position.

        Args:
            track_type: The track element to place (e.g. TrackElemType.FLAT).
            chain_lift: Whether to enable chain lift on this piece.

        Returns:
            Result with cost, new cursor position, and valid next pieces.

        Raises:
            ActionError: If the game rejects the placement.
        """
        flags = SelectedLiftAndInverted(0)
        if chain_lift:
            flags = SelectedLiftAndInverted.LIFT_HILL

        # Cursor z is the connection height. trackplace expects baseZ.
        # baseZ = connectionZ - beginZ (per TrackDesign.cpp:1617).
        begin_z = self._begin_z_lookup.get(str(int(track_type)), 0)
        placement_z = self._cursor.z - begin_z

        resp = self._client.actions.track_place(
            x=self._cursor.x,
            y=self._cursor.y,
            z=placement_z,
            direction=self._cursor.direction,
            ride=self._id,
            track_type=track_type,
            ride_type=self._ride_type,
            brake_speed=0,
            colour=0,
            seat_rotation=4,
            track_place_flags=flags,
            is_from_track_design=False,
        )

        # Update state from enriched response (track_place raises on failure,
        # so we only reach here on success)
        cursor_data = resp["cursor"]
        self._end_slope = resp["endSlope"]
        self._end_bank = resp["endBank"]
        self._valid_next = [TrackElemType(v) for v in resp["validNext"]]
        self._begin_z_lookup = resp["beginZMap"]

        # Record placed piece for undo (at placement z, not cursor z)
        self._pieces.append(
            PlacedPiece(
                track_type=track_type,
                x=self._cursor.x,
                y=self._cursor.y,
                z=placement_z,
                direction=self._cursor.direction,
            )
        )

        self._cursor = CursorPosition(
            x=cursor_data["x"],
            y=cursor_data["y"],
            z=cursor_data["z"],
            direction=Direction(cursor_data["direction"]),
        )

        result = TrackPlaceResult(
            cost=resp.get("cost", 0),
            position=self._cursor,
            valid_next=self._valid_next,
            end_slope=self._end_slope,
            end_bank=self._end_bank,
        )

        # TODO: Consider making circuit_complete a lazy property instead of
        # checking on every placement. The local check is cheap but still
        # runs on every place() call.
        self._check_circuit()

        return result

    def undo(self, n: int = 1) -> list[TrackRemoveResult]:
        """Remove the last N placed track pieces.

        Protects station pieces — cannot undo past the first station piece
        (beginStation). To relocate a ride, use ``.demolish()`` and recreate.

        Args:
            n: Number of pieces to remove (default 1).

        Returns:
            List of removal results (one per piece removed).

        Raises:
            ValueError: If n would remove station pieces.
            ActionError: If the game rejects the removal.
        """
        removable = len(self._pieces) - self._station_piece_count
        if n > removable:
            raise ValueError(
                f"Cannot undo {n} pieces — only {removable} non-station pieces placed. "
                f"Station pieces ({self._station_piece_count}) are protected."
            )

        results = []
        for _ in range(n):
            piece = self._pieces.pop()
            resp = self._client.actions.track_remove(
                x=piece.x,
                y=piece.y,
                z=piece.z,
                direction=piece.direction,
                track_type=piece.track_type,
                sequence=0,
            )
            cost = resp.get("payload", {}).get("cost", 0) if resp.get("success") else 0
            results.append(TrackRemoveResult(track_type=piece.track_type, cost=cost))

        # Resync cursor from bridge after undo
        self._resync_from_bridge()
        self._circuit_complete = False

        return results

    # ── State properties ────────────────────────────────────────────

    @property
    def position(self) -> CursorPosition:
        """Current cursor position — where the next piece will be placed."""
        return self._cursor

    @property
    def valid_next(self) -> list[TrackElemType]:
        """Track element types that can be placed at the current cursor."""
        return list(self._valid_next)

    @property
    def pieces(self) -> list[PlacedPiece]:
        """All placed track pieces (including station), in placement order."""
        return list(self._pieces)

    @property
    def circuit_complete(self) -> bool:
        """Whether the track forms a complete circuit back to the station."""
        return self._circuit_complete

    # ── Entrance / exit ─────────────────────────────────────────────

    def place_entrance(self, tile: Tile, station: int = 0) -> ActionResult:
        """Place a ride entrance on the given tile.

        Args:
            tile: The tile for the entrance (must be adjacent to a station piece).
            station: Station index (default 0, most rides have one station).

        TODO: Add defensive checks like place_flat_ride — validate tile is not
        on a station piece, is adjacent to one, and is clear of other elements.
        Currently relies on _entrance_exit_direction (adjacency) + game ActionError.
        """
        direction = self._entrance_exit_direction(tile)
        return ActionResult.from_response(
            self._client.actions.ride_entrance_exit_place(
                x=tile.x * TILE_SIZE,
                y=tile.y * TILE_SIZE,
                direction=direction,
                ride=self._id,
                station=station,
                is_exit=False,
            )
        )

    def place_exit(self, tile: Tile, station: int = 0) -> ActionResult:
        """Place a ride exit on the given tile.

        Args:
            tile: The tile for the exit (must be adjacent to a station piece).
            station: Station index (default 0, most rides have one station).

        TODO: Add defensive checks like place_flat_ride (see place_entrance).
        """
        direction = self._entrance_exit_direction(tile)
        return ActionResult.from_response(
            self._client.actions.ride_entrance_exit_place(
                x=tile.x * TILE_SIZE,
                y=tile.y * TILE_SIZE,
                direction=direction,
                ride=self._id,
                station=station,
                is_exit=True,
            )
        )

    # ── Private helpers ─────────────────────────────────────────────

    def _entrance_exit_direction(self, tile: Tile) -> Direction:
        """Compute the placement direction for an entrance/exit tile.

        Looks at station pieces to find one adjacent to the given tile,
        then derives the correct direction using the same empirical rule
        as flat rides.
        """
        station_tiles: set[Tile] = set()
        for piece in self._pieces[: self._station_piece_count]:
            station_tiles.add(Tile.from_world(piece.x, piece.y))

        # Use the flat-ride entrance direction logic
        return _entrance_direction(tile, station_tiles, self._pieces[0].direction)

    def _check_circuit(self) -> None:
        """Check circuit completion via bridge track_get_state.

        Only queries the bridge when the cursor returns to the station's
        position and direction (cheap local check). The bridge walk is O(n)
        on piece count so we avoid it on every placement.
        """
        # Quick local check: cursor must match station entry
        first = self._pieces[0]
        if (
            self._cursor.x != first.x
            or self._cursor.y != first.y
            or self._cursor.z != first.z
            or self._cursor.direction != first.direction
        ):
            self._circuit_complete = False
            return

        # Cursor matches station — confirm with bridge walk
        state = self._client.execute(
            "track_get_state",
            {"ride": self._id, "rideType": int(self._ride_type)},
        )
        self._circuit_complete = state["payload"]["circuitComplete"]

    def _resync_from_bridge(self) -> None:
        """Resync cursor and valid_next from bridge after undo."""
        state = self._client.execute(
            "track_get_state",
            {"ride": self._id, "rideType": int(self._ride_type)},
        )
        payload = state["payload"]
        cursor_data = payload.get("cursor")
        if cursor_data:
            self._cursor = CursorPosition(
                x=cursor_data["x"],
                y=cursor_data["y"],
                z=cursor_data["z"],
                direction=Direction(cursor_data["direction"]),
            )
        self._valid_next = [TrackElemType(v) for v in payload.get("validNext", [])]
        self._end_slope = payload.get("endSlope", 0)
        self._end_bank = payload.get("endBank", 0)
        self._begin_z_lookup = payload.get("beginZMap", {})


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

        valid_tiles = sorted((t.x, t.y) for t in adjacent)

        if entrance in footprint_set:
            raise ValueError(
                f"Entrance {entrance} is inside the ride footprint. "
                f"Place it on a tile adjacent to the footprint edge, not on top of it. "
                f"Valid tiles: {valid_tiles}"
            )
        if entrance not in adjacent:
            raise ValueError(
                f"Entrance {entrance} is not adjacent to the ride footprint. "
                f"Place it on a tile directly next to (not diagonal to) the footprint edge. "
                f"Valid tiles: {valid_tiles}"
            )
        if exit in footprint_set:
            raise ValueError(
                f"Exit {exit} is inside the ride footprint. "
                f"Place it on a tile adjacent to the footprint edge, not on top of it. "
                f"Valid tiles: {valid_tiles}"
            )
        if exit not in adjacent:
            raise ValueError(
                f"Exit {exit} is not adjacent to the ride footprint. "
                f"Place it on a tile directly next to (not diagonal to) the footprint edge. "
                f"Valid tiles: {valid_tiles}"
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

    def create_tracked_ride(
        self,
        obj: RideObjectInfo,
        station_origin: Tile,
        station_length: int = 3,
        direction: Direction = Direction.NORTH,
        height: int | None = None,
    ) -> TrackedRideEntity:
        """Create a tracked ride with station placed and cursor ready.

        Works for all tracked ride types: coasters, water rides, transport
        rides (mini railway), and tracked gentle rides (ghost train). The
        ride object determines which track pieces are valid.

        Station is placed as: beginStation -> middleStation x (n-2) -> endStation.
        A 1-tile station uses a single endStation piece.

        Args:
            obj: The ride object (e.g. RideObjects.rollercoaster.TWISTER_TRAINS).
            station_origin: Tile for the first station piece.
            station_length: Number of station tiles (default 3, min 1).
            direction: Station facing direction (default NORTH).
            height: Height in land steps. Defaults to surface height.

        Returns:
            A TrackedRideEntity with cursor at station exit, ready for .place().

        Raises:
            ValueError: If station_length < 1 or object is a flat ride.
            RuntimeError: If the ride object is not loaded.
            ActionError: If placement fails.
        """
        if station_length < 1:
            raise ValueError("station_length must be at least 1")

        # Reject flat rides (they have an entry in RIDE_TYPE_TRACK_ELEMS)
        if obj.ride_type in RIDE_TYPE_TRACK_ELEMS:
            raise ValueError(
                f"'{obj.name}' (ride type '{obj.ride_type}') is a flat ride. Use place_flat_ride() instead."
            )

        obj_index = self._client.objects._require_loaded_index(obj)
        ride_type = _resolve_ride_type(obj)

        # Create ride slot
        result = self._client.actions.ride_create(
            ride_type=ride_type,
            ride_object=obj_index,
            entrance_object=0,
            colour1=0,
            colour2=0,
            inspection_interval=RideInspection.EVERY30_MINUTES,
        )
        ride_id = result["payload"]["ride"]

        z = self._client.world.resolve_height(station_origin, height)

        # Place station chain: all pieces use END_STATION.
        # The game's TrackAddStationElement auto-classifies adjacent station
        # tiles into begin/middle/end based on chain position. The C++ RTD's
        # StartTrackPiece is typically endStation for tracked rides.
        station_sequence = [TrackElemType.END_STATION] * station_length

        pieces: list[PlacedPiece] = []
        cursor_x = station_origin.x * TILE_SIZE
        cursor_y = station_origin.y * TILE_SIZE
        cursor_z = z
        cursor_dir = direction
        last_resp: dict = {}

        try:
            for track_type in station_sequence:
                resp = self._client.actions.track_place(
                    x=cursor_x,
                    y=cursor_y,
                    z=cursor_z,
                    direction=cursor_dir,
                    ride=ride_id,
                    track_type=track_type,
                    ride_type=ride_type,
                    brake_speed=0,
                    colour=0,
                    seat_rotation=4,
                    track_place_flags=SelectedLiftAndInverted(0),
                    is_from_track_design=False,
                )

                pieces.append(
                    PlacedPiece(
                        track_type=track_type,
                        x=cursor_x,
                        y=cursor_y,
                        z=cursor_z,
                        direction=cursor_dir,
                    )
                )

                # Advance cursor from enriched response
                cursor_data = resp.get("cursor")
                if cursor_data:
                    cursor_x = cursor_data["x"]
                    cursor_y = cursor_data["y"]
                    cursor_z = cursor_data["z"]
                    cursor_dir = Direction(cursor_data["direction"])
                last_resp = resp
        except ActionError:
            # Clean up on failure
            self._client.actions.ride_demolish(
                ride=ride_id,
                modify_type=RideModifyType.DEMOLISH,
            )
            raise

        # Build cursor from last response
        cursor = CursorPosition(
            x=cursor_x,
            y=cursor_y,
            z=cursor_z,
            direction=cursor_dir,
        )
        valid_next = [TrackElemType(v) for v in last_resp["validNext"]]
        end_slope = last_resp["endSlope"]
        end_bank = last_resp["endBank"]
        begin_z_lookup = last_resp["beginZMap"]

        # Fetch ride data
        ride_data = self._client._query("rides", {"id": ride_id})
        ride = Ride.model_validate(ride_data)

        entity = TrackedRideEntity(
            client=self._client,
            model=ride,
            ride_type=ride_type,
            cursor=cursor,
            valid_next=valid_next,
            pieces=pieces,
            end_slope=end_slope,
            end_bank=end_bank,
        )
        entity._begin_z_lookup = begin_z_lookup
        return entity

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
    """Convert a ride object's type string to the RideType enum.

    Uses RIDE_TYPE_STR_TO_INT (generated mapping from ride_type strings
    to RideType int values) with a fallback to direct name matching.
    """
    int_val = RIDE_TYPE_STR_TO_INT.get(obj.ride_type)
    if int_val is not None:
        return RideType(int_val)
    # Fall back to direct name match
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
