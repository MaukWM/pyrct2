"""ClimateProxy — high-level access to climate state."""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from pyrct2._generated.state import WeatherState

if TYPE_CHECKING:
    from pyrct2.client import RCT2


class WeatherType(StrEnum):
    """Weather types returned by the OpenRCT2 plugin API.

    Hand-copied from the plugin API .d.ts type definition (not auto-generated).
    Maps 1:1 to C++ enum Weather::Type (0-8) in src/openrct2/world/Weather.h,
    but the scripting layer converts to strings.

    Values frozen since Sep 2020 (snow types added in PR #12922):
    https://github.com/OpenRCT2/OpenRCT2/pull/12922
    """

    SUNNY = "sunny"
    PARTIALLY_CLOUDY = "partiallyCloudy"
    CLOUDY = "cloudy"
    RAIN = "rain"
    HEAVY_RAIN = "heavyRain"
    THUNDER = "thunder"
    SNOW = "snow"
    HEAVY_SNOW = "heavySnow"
    BLIZZARD = "blizzard"


class ClimateProxy:
    """High-level climate namespace: ``game.park.climate``. Read-only."""

    def __init__(self, client: RCT2) -> None:
        self._client = client

    @property
    def weather(self) -> WeatherType:
        return WeatherType(self._client.state.climate_current().weather)

    @property
    def temperature(self) -> int:
        return self._client.state.climate_current().temperature

    @property
    def future(self) -> WeatherState:
        return self._client.state.climate_future()
