"""CheatsProxy — high-level access to game cheats."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyrct2._generated.enums import CheatType
from pyrct2._generated.state import Cheats
from pyrct2.result import ActionResult

if TYPE_CHECKING:
    from pyrct2.client import RCT2


class CheatsProxy:
    """High-level cheats namespace: ``game.park.cheats``.

    Every boolean cheat has a dedicated method with an ``active`` parameter
    (default True).
    """

    def __init__(self, client: RCT2) -> None:
        self._client = client

    def _toggle(self, cheat: CheatType, active: bool) -> ActionResult:
        return ActionResult.from_response(self._client.actions.cheat_set(type=cheat, param1=int(active), param2=0))

    def _fire(self, cheat: CheatType) -> ActionResult:
        return ActionResult.from_response(self._client.actions.cheat_set(type=cheat, param1=0, param2=0))

    def _set(self, cheat: CheatType, value: int) -> ActionResult:
        return ActionResult.from_response(self._client.actions.cheat_set(type=cheat, param1=value, param2=0))

    def list(self) -> Cheats:
        """Return all cheat flags as a Pydantic model."""
        return self._client.state.cheats()

    # -- Boolean toggles --

    def sandbox_mode(self, active: bool = True) -> ActionResult:
        return self._toggle(CheatType.SANDBOX_MODE, active)

    def disable_clearance_checks(self, active: bool = True) -> ActionResult:
        return self._toggle(CheatType.DISABLE_CLEARANCE_CHECKS, active)

    def disable_support_limits(self, active: bool = True) -> ActionResult:
        return self._toggle(CheatType.DISABLE_SUPPORT_LIMITS, active)

    def show_all_operating_modes(self, active: bool = True) -> ActionResult:
        return self._toggle(CheatType.SHOW_ALL_OPERATING_MODES, active)

    def show_vehicles_from_other_track_types(self, active: bool = True) -> ActionResult:
        return self._toggle(CheatType.SHOW_VEHICLES_FROM_OTHER_TRACK_TYPES, active)

    def disable_train_length_limit(self, active: bool = True) -> ActionResult:
        return self._toggle(CheatType.DISABLE_TRAIN_LENGTH_LIMIT, active)

    def enable_chain_lift_on_all_track(self, active: bool = True) -> ActionResult:
        return self._toggle(CheatType.ENABLE_CHAIN_LIFT_ON_ALL_TRACK, active)

    def fast_lift_hill(self, active: bool = True) -> ActionResult:
        return self._toggle(CheatType.FAST_LIFT_HILL, active)

    def disable_brakes_failure(self, active: bool = True) -> ActionResult:
        return self._toggle(CheatType.DISABLE_BRAKES_FAILURE, active)

    def disable_all_breakdowns(self, active: bool = True) -> ActionResult:
        return self._toggle(CheatType.DISABLE_ALL_BREAKDOWNS, active)

    def build_in_pause_mode(self, active: bool = True) -> ActionResult:
        return self._toggle(CheatType.BUILD_IN_PAUSE_MODE, active)

    def ignore_ride_intensity(self, active: bool = True) -> ActionResult:
        return self._toggle(CheatType.IGNORE_RIDE_INTENSITY, active)

    def disable_vandalism(self, active: bool = True) -> ActionResult:
        return self._toggle(CheatType.DISABLE_VANDALISM, active)

    def disable_littering(self, active: bool = True) -> ActionResult:
        return self._toggle(CheatType.DISABLE_LITTERING, active)

    def disable_plant_aging(self, active: bool = True) -> ActionResult:
        return self._toggle(CheatType.DISABLE_PLANT_AGING, active)

    def make_destructible(self, active: bool = True) -> ActionResult:
        return self._toggle(CheatType.MAKE_DESTRUCTIBLE, active)

    def freeze_weather(self, active: bool = True) -> ActionResult:
        return self._toggle(CheatType.FREEZE_WEATHER, active)

    def neverending_marketing(self, active: bool = True) -> ActionResult:
        return self._toggle(CheatType.NEVERENDING_MARKETING, active)

    def allow_arbitrary_ride_type_changes(self, active: bool = True) -> ActionResult:
        return self._toggle(CheatType.ALLOW_ARBITRARY_RIDE_TYPE_CHANGES, active)

    def disable_ride_value_aging(self, active: bool = True) -> ActionResult:
        return self._toggle(CheatType.DISABLE_RIDE_VALUE_AGING, active)

    def ignore_research_status(self, active: bool = True) -> ActionResult:
        return self._toggle(CheatType.IGNORE_RESEARCH_STATUS, active)

    def enable_all_drawable_track_pieces(self, active: bool = True) -> ActionResult:
        return self._toggle(CheatType.ENABLE_ALL_DRAWABLE_TRACK_PIECES, active)

    def allow_track_place_invalid_heights(self, active: bool = True) -> ActionResult:
        return self._toggle(CheatType.ALLOW_TRACK_PLACE_INVALID_HEIGHTS, active)

    def allow_regular_path_as_queue(self, active: bool = True) -> ActionResult:
        return self._toggle(CheatType.ALLOW_REGULAR_PATH_AS_QUEUE, active)

    def allow_special_colour_schemes(self, active: bool = True) -> ActionResult:
        return self._toggle(CheatType.ALLOW_SPECIAL_COLOUR_SCHEMES, active)

    def ignore_ride_price(self, active: bool = True) -> ActionResult:
        return self._toggle(CheatType.IGNORE_PRICE, active)

    # Park flag cheats — state stored in park.flags, not cheats namespace
    def no_money(self, active: bool = True) -> ActionResult:
        return self._toggle(CheatType.NO_MONEY, active)

    # NOTE: UNLOCK_ALL_PRICES (10) rejected by game with INVALID_PARAMETERS on v0.4.32.
    # May be deprecated or handled differently. Available via raw actions if needed.

    # -- One-shot actions --

    def remove_all_guests(self) -> ActionResult:
        return self._fire(CheatType.REMOVE_ALL_GUESTS)

    def water_plants(self) -> ActionResult:
        return self._fire(CheatType.WATER_PLANTS)

    def fix_vandalism(self) -> ActionResult:
        return self._fire(CheatType.FIX_VANDALISM)

    def remove_litter(self) -> ActionResult:
        return self._fire(CheatType.REMOVE_LITTER)

    def renew_rides(self) -> ActionResult:
        return self._fire(CheatType.RENEW_RIDES)

    def fix_rides(self) -> ActionResult:
        return self._fire(CheatType.FIX_RIDES)

    def reset_crash_status(self) -> ActionResult:
        return self._fire(CheatType.RESET_CRASH_STATUS)

    def ten_minute_inspections(self) -> ActionResult:
        return self._fire(CheatType.TEN_MINUTE_INSPECTIONS)

    def win_scenario(self) -> ActionResult:
        return self._fire(CheatType.WIN_SCENARIO)

    def have_fun(self) -> ActionResult:
        return self._fire(CheatType.HAVE_FUN)

    def own_all_land(self) -> ActionResult:
        return self._fire(CheatType.OWN_ALL_LAND)

    def create_ducks(self) -> ActionResult:
        return self._fire(CheatType.CREATE_DUCKS)

    def remove_ducks(self) -> ActionResult:
        return self._fire(CheatType.REMOVE_DUCKS)

    def open_close_park(self) -> ActionResult:
        return self._fire(CheatType.OPEN_CLOSE_PARK)

    def remove_park_fences(self) -> ActionResult:
        return self._fire(CheatType.REMOVE_PARK_FENCES)

    # -- Value cheats --

    def set_forced_park_rating(self, rating: int) -> ActionResult:
        """Set forced park rating (0-999). Use -1 to disable."""
        return self._set(CheatType.SET_FORCED_PARK_RATING, rating)

    def set_money(self, amount: int) -> ActionResult:
        return self._set(CheatType.SET_MONEY, amount)

    def add_money(self, amount: int) -> ActionResult:
        return self._set(CheatType.ADD_MONEY, amount)

    def clear_loan(self) -> ActionResult:
        return self._fire(CheatType.CLEAR_LOAN)

    def force_weather(self, weather_type: int) -> ActionResult:
        # TODO: generate WeatherType enum (0-8) from src/openrct2/world/Weather.h
        return self._set(CheatType.FORCE_WEATHER, weather_type)

    def generate_guests(self, count: int) -> ActionResult:
        return self._set(CheatType.GENERATE_GUESTS, count)

    def set_grass_length(self, length: int) -> ActionResult:
        # TODO: generate GrassLength enum (0-6) from src/openrct2/world/tile_element/SurfaceElement.h
        return self._set(CheatType.SET_GRASS_LENGTH, length)

    def set_staff_speed(self, speed: int) -> ActionResult:
        # TODO: Valid values: 0=frozen, 96=normal, 255=fast (raw uint8, see src/openrct2/Cheats.h), generate or make an enum?
        return self._set(CheatType.SET_STAFF_SPEED, speed)

    def give_all_guests(self, item: int) -> ActionResult:
        # Not ShopItem — uses anonymous OBJECT_* enum from src/openrct2/Cheats.h:
        # 0=MONEY, 1=PARK_MAP, 2=BALLOON, 3=UMBRELLA
        # TODO: generate GuestGiftObject enum from Cheats.h
        return self._set(CheatType.GIVE_ALL_GUESTS, item)

    def set_guest_parameter(self, parameter: int, value: int) -> ActionResult:
        # GUEST_PARAMETER_* enum (0-7) from src/openrct2/Cheats.h:
        # 0=happiness, 1=energy, 2=hunger, 3=thirst, 4=nausea,
        # 5=nausea_tolerance, 6=toilet, 7=preferred_ride_intensity
        # TODO: generate GuestParameter enum from Cheats.h
        return ActionResult.from_response(
            self._client.actions.cheat_set(type=CheatType.SET_GUEST_PARAMETER, param1=parameter, param2=value)
        )
