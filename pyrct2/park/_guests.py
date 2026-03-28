"""GuestsProxy and GuestEntity — read-only guest observation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyrct2._generated.state import Guest
from pyrct2.world import Tile

if TYPE_CHECKING:
    from pyrct2.client import RCT2


class GuestEntity:
    """Wrapper around a Guest snapshot. Read-only for now.

    All properties are accessible via ``.data`` (the Pydantic model snapshot).
    """

    def __init__(self, client: RCT2, model: Guest) -> None:
        self._client = client
        self.data = model

    def __repr__(self) -> str:
        return f"GuestEntity(#{self.data.id} {self.data.name!r})"

    @property
    def _id(self) -> int:
        if self.data.id is None:
            raise ValueError("Entity has no ID")
        return self.data.id

    @property
    def tile(self) -> Tile:
        """Tile this guest is standing on (floored from world coords)."""
        return Tile.from_world(self.data.x, self.data.y)


class GuestsProxy:
    """High-level guests namespace: ``game.park.guests``."""

    def __init__(self, client: RCT2) -> None:
        self._client = client

    def list(self) -> list[GuestEntity]:
        """Return all guests as entity wrappers."""
        return [GuestEntity(self._client, g) for g in self._client.state.guests()]

    def get(self, entity_id: int) -> GuestEntity | None:
        """Get a specific guest by entity ID, or None if not found."""
        for g in self._client.state.guests():
            if g.id == entity_id:
                return GuestEntity(self._client, g)
        return None

    def count(self) -> int:
        """Return the number of guests in the park."""
        return len(self._client.state.guests())
