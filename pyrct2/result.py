"""Typed result objects for successful game actions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ActionResult:
    """Result of a successful game action.

    If an action fails, an ActionError is raised instead — you never
    need to check for success on this object. By the time an ActionResult
    is created, the response has already passed through execute() which
    raises on any game_error.

    cost is always present because OpenRCT2's GameActions::Result has
    ``money64 cost = 0`` as a default-initialized member — every action
    result carries it, even free ones like cheats (cost=0).
    See: https://github.com/OpenRCT2/OpenRCT2/blob/develop/src/openrct2/actions/GameActionResult.h
    """

    cost: int

    @classmethod
    def from_response(cls, resp: dict) -> ActionResult:
        """Create from a raw bridge response dict.

        Only called after execute() has verified success — the response
        is guaranteed to have payload.cost at this point.
        """
        assert resp.get("success") is True, f"from_response called on non-success response: {resp}"
        return cls(cost=resp["payload"]["cost"])
