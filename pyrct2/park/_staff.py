"""StaffProxy and StaffEntity — high-level staff management."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyrct2._generated.enums import Colour, StaffSetPatrolAreaMode, StaffType
from pyrct2._generated.state import Staff
from pyrct2.result import ActionResult
from pyrct2.world import Tile

if TYPE_CHECKING:
    from pyrct2.client import RCT2


class StaffEntity:
    """Wrapper around a Staff snapshot that adds action methods.

    All properties are accessible via ``.data`` (the Pydantic model snapshot).
    Action methods send game commands via the client.
    """

    def __init__(self, client: RCT2, model: Staff) -> None:
        self._client = client
        self.data = model

    def __repr__(self) -> str:
        return f"StaffEntity({self.data.staffType} #{self.data.id} {self.data.name!r})"

    @property
    def _id(self) -> int:
        """Entity ID — always present for live entities from list()/hire().

        The API declares id as int|None because stale JS references to
        removed entities return null. We only hold live entity snapshots.
        See: https://github.com/OpenRCT2/OpenRCT2/blob/develop/src/openrct2/scripting/bindings/entity/ScEntity.hpp
        """
        if self.data.id is None:
            raise ValueError("Entity has no ID")
        return self.data.id

    # -- Read helpers --

    @property
    def tile(self) -> Tile:
        """Tile this staff member is standing on (floored from world coords)."""
        return Tile.from_world(self.data.x, self.data.y)

    # -- Write methods --

    def fire(self) -> ActionResult:
        return ActionResult.from_response(self._client.actions.staff_fire(id=self._id))

    def rename(self, name: str) -> ActionResult:
        return ActionResult.from_response(self._client.actions.staff_set_name(id=self._id, name=name))

    def set_orders(self, orders: int) -> ActionResult:
        # TODO: orders is a bitmask — generate StaffOrders flags enum from C++ source
        return ActionResult.from_response(self._client.actions.staff_set_orders(id=self._id, staff_orders=orders))

    def set_costume(self, costume: int) -> ActionResult:
        # TODO: costume is an int index — StaffCostume is a string enum in .d.ts
        # ("none", "handyman", "panda", "tiger", etc.) but the action takes an int.
        # Need to map StaffCostume strings to int indices.
        return ActionResult.from_response(self._client.actions.staff_set_costume(id=self._id, costume=costume))

    def set_colour(self, colour: Colour) -> ActionResult:
        """Set uniform colour for ALL staff of this type (game limitation)."""
        return ActionResult.from_response(
            self._client.actions.staff_set_colour(staff_type=StaffType[self.data.staffType.upper()], colour=colour)
        )

    def set_patrol_area(self, start: Tile, end: Tile) -> ActionResult:
        """Set patrol area to a rectangle, replacing any existing area."""
        self.clear_patrol_area()
        return self.add_patrol_area(start, end)

    def add_patrol_area(self, start: Tile, end: Tile) -> ActionResult:
        """Add a rectangle of tiles to the patrol area (additive)."""
        wx1, wy1 = start.to_world()
        wx2, wy2 = end.to_world()
        return ActionResult.from_response(
            self._client.actions.staff_set_patrol_area(
                id=self._id,
                x1=wx1,
                y1=wy1,
                x2=wx2,
                y2=wy2,
                mode=StaffSetPatrolAreaMode.SET,
            )
        )

    def remove_patrol_area(self, start: Tile, end: Tile) -> ActionResult:
        """Remove a rectangle of tiles from the patrol area."""
        wx1, wy1 = start.to_world()
        wx2, wy2 = end.to_world()
        return ActionResult.from_response(
            self._client.actions.staff_set_patrol_area(
                id=self._id,
                x1=wx1,
                y1=wy1,
                x2=wx2,
                y2=wy2,
                mode=StaffSetPatrolAreaMode.UNSET,
            )
        )

    def clear_patrol_area(self) -> ActionResult:
        """Clear the entire patrol area."""
        return ActionResult.from_response(
            self._client.actions.staff_set_patrol_area(
                id=self._id,
                x1=0,
                y1=0,
                x2=0,
                y2=0,
                mode=StaffSetPatrolAreaMode.CLEAR_ALL,
            )
        )

    @property
    def patrol_tiles(self) -> list[Tile]:
        """Current patrol area as a list of tiles."""
        return [Tile.from_world(c.x, c.y) for c in self.data.patrolArea.tiles]


class StaffProxy:
    """High-level staff namespace: ``game.park.staff``."""

    def __init__(self, client: RCT2) -> None:
        self._client = client

    def list(self) -> list[StaffEntity]:
        """Return all staff members as entity wrappers."""
        return [StaffEntity(self._client, s) for s in self._client.state.staff()]

    def get(self, entity_id: int) -> StaffEntity | None:
        """Get a specific staff member by entity ID, or None if not found."""
        for s in self._client.state.staff():
            if s.id == entity_id:
                return StaffEntity(self._client, s)
        return None

    def hire(self, staff_type: StaffType, costume_index: int = 0, staff_orders: int = 0) -> StaffEntity:
        """Hire a new staff member and return the entity.

        costume_index and staff_orders are raw ints for now.
        """
        # TODO: costume_index should use StaffCostume enum (string → int mapping needed)
        # TODO: staff_orders should use StaffOrders flags enum
        resp = self._client.actions.staff_hire_new(
            auto_position=True,
            staff_type=staff_type,
            costume_index=costume_index,
            staff_orders=staff_orders,
        )
        peep_id = resp["payload"]["peep"]
        for s in self._client.state.staff():
            if s.id == peep_id:
                return StaffEntity(self._client, s)
        raise RuntimeError(f"Hired staff (peep={peep_id}) not found in entity list")
