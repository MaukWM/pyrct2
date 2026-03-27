"""FinanceProxy — high-level access to park finances."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyrct2.client import RCT2


class FinanceProxy:
    """High-level finance namespace: ``game.park.finance``."""

    def __init__(self, client: RCT2) -> None:
        self._client = client

    # -- Read properties --

    @property
    def cash(self) -> int:
        return self._client.state.park_cash()

    @property
    def loan(self) -> int:
        return self._client.state.park_bank_loan()

    @property
    def max_loan(self) -> int:
        return self._client.state.park_max_bank_loan()

    @property
    def entrance_fee(self) -> int:
        return self._client.state.park_entrance_fee()

    # -- Write methods --

    def set_entrance_fee(self, amount: int) -> dict:
        return self._client.actions.park_set_entrance_fee(value=amount)

    def set_loan(self, amount: int) -> dict:
        return self._client.actions.park_set_loan(value=amount)

    def take_loan(self, amount: int) -> dict:
        new_loan = self.loan + amount
        return self._client.actions.park_set_loan(value=new_loan)

    def repay_loan(self, amount: int) -> dict:
        new_loan = self.loan - amount
        return self._client.actions.park_set_loan(value=new_loan)
