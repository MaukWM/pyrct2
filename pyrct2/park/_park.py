"""ParkProxy — high-level read/write access to park state."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

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
from pyrct2._generated.enums import Direction
from pyrct2.world._tile import DIR_DELTA, Tile

if TYPE_CHECKING:
    from pyrct2.client import RCT2


class ParkEntrance(BaseModel):
    """A park entrance gate.

    Park entrances span 3 tiles (center + 2 sides) and have no footpath
    on them. ``arrival_tile`` is the owned tile just inside the gate —
    the first tile guests step onto when entering the park. It should
    have a path on it, but that's not guaranteed (paths can be removed).
    """

    model_config = ConfigDict(frozen=True)

    tiles: list[Tile]
    arrival_tile: Tile


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
        self._entrances = self._find_entrances()
        self.cheats = CheatsProxy(client)
        self.climate = ClimateProxy(client)
        self.finance = FinanceProxy(client)
        self.guests = GuestsProxy(client)
        self.marketing = MarketingProxy(client)
        self.research = ResearchProxy(client)
        self.staff = StaffProxy(client)

    def _find_entrances(self) -> list[ParkEntrance]:
        """Query the bridge for park entrance gates.

        Uses get_elements_by_type to fetch only entrance elements, then
        groups them into ParkEntrance objects on the Python side.
        """
        park_entrance_object = 2
        raw = self._client.world.get_elements_by_type("entrance")

        # Index park-entrance elements by tile coordinate.
        by_tile: dict[tuple[int, int], list[tuple[int, Direction]]] = {}
        for e in raw:
            if e.get("object") == park_entrance_object:
                key = (e["tileX"], e["tileY"])
                by_tile.setdefault(key, []).append((e["sequence"], Direction(e["direction"])))

        # Build one ParkEntrance per center tile (sequence 0).
        result: list[ParkEntrance] = []
        for (tx, ty), elems in by_tile.items():
            for seq, direction in elems:
                if seq != 0:
                    continue
                tiles = [Tile(tx, ty)] + [
                    Tile(*k) for k in by_tile if k != (tx, ty) and abs(k[0] - tx) + abs(k[1] - ty) == 1
                ]
                dx, dy = DIR_DELTA[direction]
                result.append(
                    ParkEntrance(
                        tiles=tiles,
                        arrival_tile=Tile(tx + dx, ty + dy),
                    )
                )
        return result

    @property
    def entrances(self) -> list[ParkEntrance]:
        """Park entrance gates (computed once at init, never changes)."""
        return list(self._entrances)

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
