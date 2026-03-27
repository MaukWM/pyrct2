# Re-export all enums (generated + hand-written) as the public API.
# Usage: from pyrct2.enums import RideType, WeatherType, ...
#
# Generated enums come from openrct2-codegen. Hand-written enums are
# maintained manually but exported here so the import path is stable —
# if a hand-written enum gets generated later, it moves to _generated
# and this file doesn't change.
from pyrct2._generated.enums import *  # noqa: F401,F403
from pyrct2._generated.enums import GENERATED_OPENRCT2_VERSION  # noqa: F401

# Hand-written enums (not auto-generated, maintained manually)
from pyrct2.errors import ActionStatus  # noqa: F401
from pyrct2.park._climate import WeatherType  # noqa: F401
from pyrct2.park._research import ResearchCategory, ResearchStage  # noqa: F401
