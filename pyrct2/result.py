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

    C++ GameActions::Result always initializes ``money64 cost = 0``
    (GameActionResult.h:65), and standard actions set it explicitly.
    However, the plugin API types cost as optional (``cost?: number``
    in openrct2.d.ts:1612) because ScriptEngine.cpp:1210 conditionally
    omits it when ``cost == kMoney64Undefined``. So we default to 0.
    """

    cost: int

    @classmethod
    def from_response(cls, resp: dict) -> ActionResult:
        """Create from a raw bridge response dict.

        Only called after execute() has verified success.
        """
        assert resp.get("success") is True, f"from_response called on non-success response: {resp}"
        # Defensive: ScriptEngine.cpp:1210 skips cost when kMoney64Undefined
        return cls(cost=resp.get("payload", {}).get("cost", 0))
