"""ParkProxy — high-level read/write access to park state."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyrct2._generated.enums import ParkParameter
from pyrct2._generated.state import GameDate, ScenarioObjective
from pyrct2.park._cheats import CheatsProxy
from pyrct2.park._climate import ClimateProxy
from pyrct2.park._finance import FinanceProxy
from pyrct2.park._guests import GuestsProxy
from pyrct2.park._marketing import MarketingProxy
from pyrct2.park._research import ResearchProxy
from pyrct2.park._staff import StaffProxy
from pyrct2.result import ActionResult
from pyrct2.world._tile import Tile

if TYPE_CHECKING:
    from pyrct2.client import RCT2

# EntranceElement.object values (from C++ EntranceElement.h):
# 0 = ride entrance, 1 = ride exit, 2 = park entrance
_PARK_ENTRANCE_OBJECT = 2


class ParkProxy:
    """High-level park namespace: ``game.park``."""

    cheats: CheatsProxy
    climate: ClimateProxy
    finance: FinanceProxy
    guests: GuestsProxy
    marketing: MarketingProxy
    research: ResearchProxy
    staff: StaffProxy

    def __init__(self, client: RCT2) -> None:
        self._client = client
        self._park_entrance_tiles = self._find_park_entrance_tiles()
        self.cheats = CheatsProxy(client)
        self.climate = ClimateProxy(client)
        self.finance = FinanceProxy(client)
        self.guests = GuestsProxy(client)
        self.marketing = MarketingProxy(client)
        self.research = ResearchProxy(client)
        self.staff = StaffProxy(client)

    def _find_park_entrance_tiles(self) -> list[Tile]:
        bounds = self._client.world.get_bounds()
        tiles = self._client.world.get_tiles(Tile(0, 0), Tile(bounds.x - 1, bounds.y - 1))
        return [
            Tile(t.x, t.y)
            for t in tiles
            for e in t.entrances
            if e.object == _PARK_ENTRANCE_OBJECT and e.sequence == 0
        ]

    @property
    def park_entrance_tiles(self) -> list[Tile]:
        """Park entrance gate locations (computed once at init, never changes)."""
        return list(self._park_entrance_tiles)

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

    def set_name(self, name: str) -> ActionResult:
        return ActionResult.from_response(self._client.actions.park_set_name(name=name))

    def open(self) -> ActionResult:
        return ActionResult.from_response(
            self._client.actions.park_set_parameter(parameter=ParkParameter.OPEN, value=1)
        )

    def close(self) -> ActionResult:
        return ActionResult.from_response(
            self._client.actions.park_set_parameter(parameter=ParkParameter.CLOSE, value=0)
        )
