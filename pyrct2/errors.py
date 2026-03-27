"""pyrct2 exception hierarchy."""

from __future__ import annotations


class RCT2Error(Exception):
    """Base exception for all pyrct2 errors."""


class ActionError(RCT2Error):
    """The game rejected an action (e.g. insufficient funds, invalid params)."""

    def __init__(
        self,
        *,
        status: int,
        title: str,
        message: str,
        cost: int | None = None,
        action: str | None = None,
        params: dict | None = None,
    ) -> None:
        self.status = status
        self.title = title
        self.message = message
        self.cost = cost
        self.action = action
        self.params = params
        super().__init__(f"{title}: {message}")
