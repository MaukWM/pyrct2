"""GuestsProxy, GuestEntity, and GuestSummary — guest observation and interaction."""

from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING

from pydantic import BaseModel

from pyrct2._generated.state import Guest
from pyrct2._peep import PeepEntity
from pyrct2.errors import QueryError
from pyrct2.result import ActionResult

if TYPE_CHECKING:
    from pyrct2.client import RCT2


class GuestSummary(BaseModel):
    """Aggregated snapshot of all guests in the park.

    Variables here are only slightly arbitrarily decided, might be changes/additions later.
    """

    count: int
    in_park: int
    lost: int
    avg_happiness: float
    avg_nausea: float
    avg_hunger: float
    avg_thirst: float
    avg_energy: float
    avg_toilet: float
    thoughts: dict[str, int]  # TODO: replace str key with ThoughtType StrEnum once codegen supports it


class GuestEntity(PeepEntity):
    """Wrapper around a Guest snapshot.

    All properties are accessible via ``.data`` (the Pydantic model snapshot).
    Inherits tile and move_to from PeepEntity.
    """

    def __repr__(self) -> str:
        return f"GuestEntity(#{self.data.id} {self.data.name!r})"

    def rename(self, name: str) -> ActionResult:
        """Rename this guest."""
        return ActionResult.from_response(
            self._client.actions.guest_set_name(
                peep=self._id,
                name=name,
            )
        )

    def refresh(self) -> None:
        """Re-fetch this guest's state from the game.

        Warning: entity IDs are reused. If this guest has left the park and a
        new guest received the same ID, this will silently load the wrong data.
        """
        guest_data = self._client._query("guests", {"id": self._id})
        self.data = Guest.model_validate(guest_data)


class GuestsProxy:
    """High-level guests namespace: ``game.park.guests``."""

    def __init__(self, client: RCT2) -> None:
        self._client = client

    def list(self) -> list[GuestEntity]:
        """Return all guests as entity wrappers."""
        return [GuestEntity(self._client, g) for g in self._client.state.guests()]

    def get(self, entity_id: int) -> GuestEntity | None:
        """Get a specific guest by entity ID, or None if not found."""
        try:
            guest_data = self._client._query("guests", {"id": entity_id})
        except QueryError as e:
            if e.error == "not_found":
                return None
            raise
        guest = Guest.model_validate(guest_data)
        return GuestEntity(self._client, guest)

    def count(self) -> int:
        """Return the number of guests in the park."""
        return len(self._client.state.guests())

    def summary(self) -> GuestSummary:
        """Compute an aggregated snapshot of all guests."""
        guests = self._client.state.guests()
        n = len(guests)
        if n == 0:
            return GuestSummary(
                count=0,
                in_park=0,
                lost=0,
                avg_happiness=0,
                avg_nausea=0,
                avg_hunger=0,
                avg_thirst=0,
                avg_energy=0,
                avg_toilet=0,
                thoughts={},
            )

        def _avg(attr: str) -> float:
            return sum(getattr(g, attr) for g in guests) / n

        thoughts = Counter(t.type for g in guests for t in g.thoughts)

        return GuestSummary(
            count=n,
            in_park=sum(g.isInPark for g in guests),
            lost=sum(g.isLost for g in guests),
            avg_happiness=_avg("happiness"),
            avg_nausea=_avg("nausea"),
            avg_hunger=_avg("hunger"),
            avg_thirst=_avg("thirst"),
            avg_energy=_avg("energy"),
            avg_toilet=_avg("toilet"),
            thoughts=thoughts,
        )
