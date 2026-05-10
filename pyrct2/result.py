"""Typed result objects for successful game actions."""

from __future__ import annotations

from dataclasses import dataclass, field

from pyrct2._generated.enums import Direction, TrackElemType


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


# ── Track building results ──────────────────────────────────────────


@dataclass(frozen=True)
class CursorPosition:
    """Next placement position after a track piece.

    Coordinates are in world units (32 per tile, 8 per height step).
    z is the connection height — pyrct2 subtracts beginZ before placement.
    """

    x: int
    y: int
    z: int
    direction: Direction


@dataclass(frozen=True)
class PlacedPiece:
    """Record of a placed track piece, used for undo."""

    track_type: TrackElemType
    x: int
    y: int
    z: int
    direction: Direction


@dataclass(frozen=True)
class TrackPlaceResult:
    """Result of placing a track piece via TrackedRideEntity.place()."""

    cost: int
    position: CursorPosition
    valid_next: list[TrackElemType] = field(default_factory=list)
    end_slope: int = 0
    end_bank: int = 0

    @classmethod
    def from_response(cls, resp: dict, cursor: dict, valid_next: list[int]) -> TrackPlaceResult:
        """Create from an enriched bridge trackplace response."""
        return cls(
            cost=resp.get("cost", 0),
            position=CursorPosition(
                x=cursor["x"],
                y=cursor["y"],
                z=cursor["z"],
                direction=Direction(cursor["direction"]),
            ),
            valid_next=[TrackElemType(v) for v in valid_next],
            end_slope=resp.get("endSlope", 0),
            end_bank=resp.get("endBank", 0),
        )


@dataclass(frozen=True)
class TrackRemoveResult:
    """Result of removing a track piece via undo()."""

    track_type: TrackElemType
    cost: int
