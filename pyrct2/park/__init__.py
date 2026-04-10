"""High-level park management API."""

from pyrct2.park._cheats import CheatsProxy
from pyrct2.park._climate import ClimateProxy
from pyrct2.park._finance import FinanceProxy
from pyrct2.park._guests import GuestEntity, GuestsProxy, GuestSummary
from pyrct2.park._park import ParkProxy
from pyrct2.park._paths import LineResult, PathsProxy
from pyrct2.park._research import ResearchProxy
from pyrct2.park._rides import RideEntity, RidesProxy, StationAccess
from pyrct2.park._staff import StaffEntity, StaffProxy

__all__ = [
    "CheatsProxy",
    "ClimateProxy",
    "FinanceProxy",
    "GuestEntity",
    "GuestsProxy",
    "GuestSummary",
    "LineResult",
    "PathsProxy",
    "ParkProxy",
    "ResearchProxy",
    "RideEntity",
    "RidesProxy",
    "StaffEntity",
    "StaffProxy",
    "StationAccess",
]
