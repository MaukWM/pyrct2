"""ResearchProxy — high-level access to research state."""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from pyrct2._generated.enums import ResearchFundingLevel
from pyrct2._generated.state import ResearchItem

if TYPE_CHECKING:
    from pyrct2.client import RCT2


class ResearchStage(StrEnum):
    """Research funding stages from the OpenRCT2 plugin API.

    Hand-copied from openrct2.d.ts ResearchFundingStage type definition.
    """

    INITIAL_RESEARCH = "initial_research"
    DESIGNING = "designing"
    COMPLETING_DESIGN = "completing_design"
    UNKNOWN = "unknown"
    FINISHED_ALL = "finished_all"


class ResearchCategory(StrEnum):
    """Research priority categories from the OpenRCT2 plugin API.

    Hand-copied from openrct2.d.ts ResearchCategory type definition.
    Each category corresponds to a bit in the priorities bitmask (bit 0 = transport, ..., bit 6 = scenery).
    """

    TRANSPORT = "transport"
    GENTLE = "gentle"
    ROLLERCOASTER = "rollercoaster"
    THRILL = "thrill"
    WATER = "water"
    SHOP = "shop"
    SCENERY = "scenery"


class ResearchProxy:
    """High-level research namespace: ``game.park.research``. Read-only for now."""

    def __init__(self, client: RCT2) -> None:
        self._client = client

    @property
    def invented_items(self) -> list[ResearchItem]:
        return self._client.state.park_research().inventedItems

    @property
    def uninvented_items(self) -> list[ResearchItem]:
        return self._client.state.park_research().uninventedItems

    @property
    def expected_item(self) -> ResearchItem | None:
        return self._client.state.park_research().expectedItem

    @property
    def last_researched_item(self) -> ResearchItem | None:
        return self._client.state.park_research().lastResearchedItem

    @property
    def progress(self) -> int:
        return self._client.state.park_research().progress

    @property
    def funding(self) -> ResearchFundingLevel:
        return ResearchFundingLevel(self._client.state.park_research().funding)

    @property
    def priorities(self) -> list[ResearchCategory]:
        return [ResearchCategory(p) for p in self._client.state.park_research().priorities]

    @property
    def stage(self) -> ResearchStage:
        return ResearchStage(self._client.state.park_research().stage)

    # TODO: set_funding(ResearchFundingLevel) — needs bitmask conversion for priorities
    # TODO: set_priorities(...) — needs bitmask conversion + enum for categories
