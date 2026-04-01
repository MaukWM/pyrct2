"""pyrct2 exception hierarchy."""

from __future__ import annotations

from enum import IntEnum


class ActionStatus(IntEnum):
    """OpenRCT2 GameActions::Status codes returned when an action is rejected.

    Hand-copied from OpenRCT2 C++ source (not auto-generated).

    Last value addition (NOT_CLOSED, BROKEN) was Feb 2019:
    https://github.com/OpenRCT2/OpenRCT2/commit/c1546a92b7be8d29e214c19975f8bbb8bd47c91f
    Only cosmetic renames since then — last change was casing convention (Dec 2025):
    https://github.com/OpenRCT2/OpenRCT2/commit/5ffee91

    Source: https://github.com/OpenRCT2/OpenRCT2/blob/develop/src/openrct2/actions/GameActionResult.h
    """

    OK = 0
    INVALID_PARAMETERS = 1
    DISALLOWED = 2
    GAME_PAUSED = 3
    INSUFFICIENT_FUNDS = 4
    NOT_IN_EDITOR_MODE = 5
    NOT_OWNED = 6
    TOO_LOW = 7
    TOO_HIGH = 8
    NO_CLEARANCE = 9
    ITEM_ALREADY_PLACED = 10
    NOT_CLOSED = 11
    BROKEN = 12
    NO_FREE_ELEMENTS = 13
    UNKNOWN = 65535


class RCT2Error(Exception):
    """Base exception for all pyrct2 errors."""


class QueryError(RCT2Error):
    """A bridge query returned a non-success response."""

    def __init__(self, endpoint: str, error: str, message: str | None = None) -> None:
        self.endpoint = endpoint
        self.error = error
        self.error_message = message
        super().__init__(f"Query {endpoint!r} failed: {error}" + (f" — {message}" if message else ""))


class ActionError(RCT2Error):
    """The game rejected an action (e.g. insufficient funds, invalid params)."""

    def __init__(
        self,
        *,
        status: ActionStatus,
        title: str | None = None,
        message: str | None = None,
        cost: int | None = None,
        action: str | None = None,
        params: dict | None = None,
    ) -> None:
        self.status = ActionStatus(status)
        self.title = title
        self.message = message
        self.cost = cost
        self.action = action
        self.params = params
        super().__init__(f"[{self.status.name}] {title}: {message}")
