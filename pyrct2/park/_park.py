"""ParkProxy — high-level read/write access to park state."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from pyrct2._generated.enums import Direction, ParkParameter
from pyrct2._generated.state import GameDate, ScenarioObjective
from pyrct2.park._cheats import CheatsProxy
from pyrct2.park._climate import ClimateProxy
from pyrct2.park._finance import FinanceProxy
from pyrct2.park._guests import GuestsProxy
from pyrct2.park._marketing import MarketingProxy
from pyrct2.park._research import ResearchProxy
from pyrct2.park._staff import StaffProxy
from pyrct2.result import ActionResult
from pyrct2.world._tile import DIR_DELTA, Tile

if TYPE_CHECKING:
    from pyrct2.client import RCT2

# EntranceElement.object values (from C++ EntranceElement.h):
# 0 = ride entrance, 1 = ride exit, 2 = park entrance
_PARK_ENTRANCE_OBJECT = 2


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
        """Scan the map once at init to find all park entrance gates."""
        bounds = self._client.world.get_bounds()
        all_tiles = self._client.world.get_tiles(Tile(0, 0), Tile(bounds.x - 1, bounds.y - 1))

        # Index every park-entrance element by tile.
        entrance_elems: dict[Tile, list[tuple[int, int]]] = {}  # tile → [(seq, direction)]
        for t in all_tiles:
            for e in t.entrances:
                if e.object == _PARK_ENTRANCE_OBJECT:
                    tile = Tile(t.x, t.y)
                    entrance_elems.setdefault(tile, []).append((e.sequence, e.direction))

        # Each park entrance spans 3 tiles. The EntranceElement.sequence
        # field identifies which part: 0 = center, 1 and 2 = sides.
        # Build one ParkEntrance per center tile.
        result: list[ParkEntrance] = []
        for tile, elems in entrance_elems.items():
            for seq, direction in elems:
                if seq != 0:
                    continue
                # Collect the 3 tiles: center + neighbors that are also park entrances.
                tiles = [tile] + [t for t in entrance_elems if t != tile and tile.distance_to(t) == 1]
                dx, dy = DIR_DELTA[Direction(direction)]
                result.append(
                    ParkEntrance(
                        tiles=tiles,
                        arrival_tile=Tile(tile.x + dx, tile.y + dy),
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
