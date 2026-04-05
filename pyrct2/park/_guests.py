"""GuestsProxy and GuestEntity — guest observation and interaction."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyrct2._peep import PeepEntity

if TYPE_CHECKING:
    from pyrct2.client import RCT2


class GuestEntity(PeepEntity):
    """Wrapper around a Guest snapshot.

    All properties are accessible via ``.data`` (the Pydantic model snapshot).
    Inherits tile and move_to from PeepEntity.
    """

    def __repr__(self) -> str:
        return f"GuestEntity(#{self.data.id} {self.data.name!r})"

    def refresh(self) -> None:
        """Re-fetch this guest's state from the game."""
        for g in self._client.state.guests():
            if g.id == self._id:
                self.data = g
                return


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
