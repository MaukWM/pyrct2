"""ResearchProxy — high-level access to research state."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyrct2._generated.state import ResearchItem

if TYPE_CHECKING:
    from pyrct2.client import RCT2


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
    def funding(self) -> int:
        return self._client.state.park_research().funding

    @property
    def priorities(self) -> list[str]:
        return self._client.state.park_research().priorities

    @property
    def stage(self) -> str:
        return self._client.state.park_research().stage

    # TODO: set_funding(ResearchFundingLevel) — needs bitmask conversion for priorities
    # TODO: set_priorities(...) — needs bitmask conversion + enum for categories
