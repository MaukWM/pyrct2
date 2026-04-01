"""RidesProxy — ride placement and management."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyrct2._generated.enums import (
    Direction,
    RideInspection,
    RideStatus,
    RideType,
    SelectedLiftAndInverted,
    TrackElemType,
)
from pyrct2._generated.objects import RIDE_TYPE_TRACK_ELEMS, RideObjectInfo
from pyrct2.result import ActionResult
from pyrct2.world._slope import LAND_HEIGHT_STEP
from pyrct2.world._tile import TILE_SIZE, Tile

if TYPE_CHECKING:
    from pyrct2.client import RCT2


class RidesProxy:
    """Ride placement and management: ``game.rides``."""

    def __init__(self, client: RCT2) -> None:
        self._client = client

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

        The tile is the center of the ride's footprint. For a 3x3 ride like
        a Merry-Go-Round placed at (20, 20), the footprint occupies
        (19,19) to (21,21). Entrance and exit must be adjacent to the
        footprint edge.

        Args:
            obj: The ride object to place (e.g. RideObjects.gentle.MERRY_GO_ROUND).
            tile: The center tile to place the ride on.
            entrance: The tile for the entrance (must be adjacent to footprint).
            exit: The tile for the exit (must be adjacent to footprint).
            height: Height in land steps. Defaults to the surface height of the tile.
            direction: Facing direction of the ride. Defaults to NORTH.

        Returns:
            The ride ID (int) for use with open(), demolish(), etc.

        Raises:
            RuntimeError: If the ride object is not loaded in the scenario.
            ValueError: If height is below the surface, or no track type found.
            ActionError: If placement fails (terrain, clearance, ownership, etc.).
        """
        # Step 1: Resolve object index
        obj_index = self._client.objects._require_loaded_index(obj)

        # Step 2: Resolve ride type and track type
        ride_type = _resolve_ride_type(obj)
        track_type = _resolve_track_type(obj)

        # Step 3: Create ride (free — just allocates a slot)
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

        # TODO: Add rollback/transaction support. If track_place or entrance/exit
        # placement fails after ride_create, the ride slot is orphaned. A general
        # transaction pattern (context manager?) would auto-demolish on failure.
        # For now, failures leave an orphaned ride that the developer must clean up.

        # Step 4: Resolve height
        surface_z = self._client.world.get_tile(tile).surface.baseZ
        if height is not None:
            z = height * LAND_HEIGHT_STEP
            if z < surface_z:
                raise ValueError(
                    f"Height {height} land steps (z={z}) is below the surface at "
                    f"tile ({tile.x}, {tile.y}) which is at {surface_z // LAND_HEIGHT_STEP} "
                    f"land steps (z={surface_z}). Raise the land first or use a higher value."
                )
        else:
            z = surface_z

        # Step 5: Place track (this is where money is spent)
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

        # Step 6: Place entrance and exit
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


# ── Helpers ───────────────────────────────────────────────────────────


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
