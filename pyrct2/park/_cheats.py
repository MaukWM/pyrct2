"""CheatsProxy — high-level access to game cheats."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyrct2._generated.enums import CheatType
from pyrct2._generated.state import Cheats

if TYPE_CHECKING:
    from pyrct2.client import RCT2


class CheatsProxy:
    """High-level cheats namespace: ``game.park.cheats``.

    Every boolean cheat has a dedicated method with an ``enabled`` parameter
    (default True).
    """

    def __init__(self, client: RCT2) -> None:
        self._client = client

    def _toggle(self, cheat: CheatType, enabled: bool) -> dict:
        return self._client.actions.cheat_set(type=cheat, param1=int(enabled), param2=0)

    def list(self) -> Cheats:
        """Return all cheat flags as a Pydantic model."""
        return self._client.state.cheats()

    # -- Boolean toggles --

    def sandbox_mode(self, enabled: bool = True) -> dict:
        return self._toggle(CheatType.SANDBOX_MODE, enabled)

    def disable_clearance_checks(self, enabled: bool = True) -> dict:
        return self._toggle(CheatType.DISABLE_CLEARANCE_CHECKS, enabled)

    def disable_support_limits(self, enabled: bool = True) -> dict:
        return self._toggle(CheatType.DISABLE_SUPPORT_LIMITS, enabled)

    def show_all_operating_modes(self, enabled: bool = True) -> dict:
        return self._toggle(CheatType.SHOW_ALL_OPERATING_MODES, enabled)

    def show_vehicles_from_other_track_types(self, enabled: bool = True) -> dict:
        return self._toggle(CheatType.SHOW_VEHICLES_FROM_OTHER_TRACK_TYPES, enabled)

    def disable_train_length_limit(self, enabled: bool = True) -> dict:
        return self._toggle(CheatType.DISABLE_TRAIN_LENGTH_LIMIT, enabled)

    def enable_chain_lift_on_all_track(self, enabled: bool = True) -> dict:
        return self._toggle(CheatType.ENABLE_CHAIN_LIFT_ON_ALL_TRACK, enabled)

    def fast_lift_hill(self, enabled: bool = True) -> dict:
        return self._toggle(CheatType.FAST_LIFT_HILL, enabled)

    def disable_brakes_failure(self, enabled: bool = True) -> dict:
        return self._toggle(CheatType.DISABLE_BRAKES_FAILURE, enabled)

    def disable_all_breakdowns(self, enabled: bool = True) -> dict:
        return self._toggle(CheatType.DISABLE_ALL_BREAKDOWNS, enabled)

    def build_in_pause_mode(self, enabled: bool = True) -> dict:
        return self._toggle(CheatType.BUILD_IN_PAUSE_MODE, enabled)

    def ignore_ride_intensity(self, enabled: bool = True) -> dict:
        return self._toggle(CheatType.IGNORE_RIDE_INTENSITY, enabled)

    def disable_vandalism(self, enabled: bool = True) -> dict:
        return self._toggle(CheatType.DISABLE_VANDALISM, enabled)

    def disable_littering(self, enabled: bool = True) -> dict:
        return self._toggle(CheatType.DISABLE_LITTERING, enabled)

    def disable_plant_aging(self, enabled: bool = True) -> dict:
        return self._toggle(CheatType.DISABLE_PLANT_AGING, enabled)

    def make_destructible(self, enabled: bool = True) -> dict:
        return self._toggle(CheatType.MAKE_DESTRUCTIBLE, enabled)

    def freeze_weather(self, enabled: bool = True) -> dict:
        return self._toggle(CheatType.FREEZE_WEATHER, enabled)

    def neverending_marketing(self, enabled: bool = True) -> dict:
        return self._toggle(CheatType.NEVERENDING_MARKETING, enabled)

    def allow_arbitrary_ride_type_changes(self, enabled: bool = True) -> dict:
        return self._toggle(CheatType.ALLOW_ARBITRARY_RIDE_TYPE_CHANGES, enabled)

    def disable_ride_value_aging(self, enabled: bool = True) -> dict:
        return self._toggle(CheatType.DISABLE_RIDE_VALUE_AGING, enabled)

    def ignore_research_status(self, enabled: bool = True) -> dict:
        return self._toggle(CheatType.IGNORE_RESEARCH_STATUS, enabled)

    def enable_all_drawable_track_pieces(self, enabled: bool = True) -> dict:
        return self._toggle(CheatType.ENABLE_ALL_DRAWABLE_TRACK_PIECES, enabled)

    def allow_track_place_invalid_heights(self, enabled: bool = True) -> dict:
        return self._toggle(CheatType.ALLOW_TRACK_PLACE_INVALID_HEIGHTS, enabled)

    def allow_regular_path_as_queue(self, enabled: bool = True) -> dict:
        return self._toggle(CheatType.ALLOW_REGULAR_PATH_AS_QUEUE, enabled)

    def allow_special_colour_schemes(self, enabled: bool = True) -> dict:
        return self._toggle(CheatType.ALLOW_SPECIAL_COLOUR_SCHEMES, enabled)

    def ignore_ride_price(self, enabled: bool = True) -> dict:
        return self._toggle(CheatType.IGNORE_PRICE, enabled)
