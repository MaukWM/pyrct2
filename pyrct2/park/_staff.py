"""StaffProxy and StaffEntity — high-level staff management."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyrct2._generated.enums import Colour, StaffSetPatrolAreaMode, StaffType
from pyrct2._generated.state import Staff
from pyrct2.result import ActionResult

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
        """Entity ID — always present for spawned entities."""
        if self.data.id is None:
            raise ValueError("Entity has no ID")
        return self.data.id

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

    def set_patrol(self, x1: int, y1: int, x2: int, y2: int, mode: StaffSetPatrolAreaMode) -> ActionResult:
        return ActionResult.from_response(
            self._client.actions.staff_set_patrol_area(id=self._id, x1=x1, y1=y1, x2=x2, y2=y2, mode=mode)
        )


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
