"""ParkProxy — high-level read/write access to park state."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyrct2._generated.enums import ParkParameter
from pyrct2._generated.state import GameDate, ScenarioObjective
from pyrct2.park._finance import FinanceProxy

if TYPE_CHECKING:
    from pyrct2.client import RCT2


class ParkProxy:
    """High-level park namespace: ``game.park``."""

    finance: FinanceProxy

    def __init__(self, client: RCT2) -> None:
        self._client = client
        self.finance = FinanceProxy(client)

    # -- Read properties

    @property
    def name(self) -> str:
        return self._client.state.park_name()

    @property
    def rating(self) -> int:
        return self._client.state.park_rating()

    @property
    def value(self) -> int:
        return self._client.state.park_value()

    @property
    def date(self) -> GameDate:
        return self._client.state.date()

    @property
    def objective(self) -> ScenarioObjective:
        return self._client.state.scenario_objective()

    @property
    def is_open(self) -> bool:
        return self._client.state.park_flags().open

    # -- Write methods --

    def set_name(self, name: str) -> dict:
        return self._client.actions.park_set_name(name=name)

    def open(self) -> dict:
        return self._client.actions.park_set_parameter(
            parameter=ParkParameter.OPEN,
            value=1,
        )

    def close(self) -> dict:
        return self._client.actions.park_set_parameter(
            parameter=ParkParameter.CLOSE,
            value=0,
        )
