# Re-export generated enums as the public API.
# Usage: from pyrct2.enums import RideType, Direction, ...
from pyrct2._generated.enums import *  # noqa: F401,F403
from pyrct2._generated.enums import GENERATED_OPENRCT2_VERSION  # noqa: F401
