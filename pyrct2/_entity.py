"""Base class for all entity wrappers (rides, guests, staff, etc.)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pyrct2.client import RCT2


class EntityBase:
    """Base for entity wrappers that hold a state snapshot + client reference.

    All OpenRCT2 entities have an ID. Subclasses add domain-specific
    properties and write methods. Each subclass implements its own
    refresh() to re-fetch state from the game.
    """

    def __init__(self, client: RCT2, model: Any) -> None:
        self._client = client
        self.data: Any = model

    @property
    def _id(self) -> int:
        if self.data.id is None:
            raise ValueError("Entity has no ID")
        return self.data.id
