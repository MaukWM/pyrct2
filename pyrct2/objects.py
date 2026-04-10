"""ObjectsProxy — manage loaded game objects.

Also re-exports object catalogs as the public API:
    from pyrct2.objects import RideObjects, FootpathAdditions, ...
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pyrct2._generated.objects import (  # noqa: F401
    FootpathAdditionInfo,
    FootpathAdditions,
    FootpathRailingsInfo,
    FootpathRailings,
    FootpathSurfaceInfo,
    FootpathSurfaces,
    ObjectInfo,
    RideObjectInfo,
    RideObjects,
)
from pyrct2.errors import QueryError

if TYPE_CHECKING:
    from pyrct2.client import RCT2


class ObjectsProxy:
    """Object management: ``game.objects``."""

    def __init__(self, client: RCT2) -> None:
        self._client = client

    def get(self, obj: RideObjectInfo) -> dict[str, Any]:
        """Get runtime info for a loaded object from the bridge.

        Returns the bridge's full dump for this object (index, identifier,
        name, and type-specific fields like rideType for rides).

        Raises RuntimeError if the object is not loaded.
        """
        return self._client._query(
            "get_object",
            {"type": _object_type(obj), "identifier": obj.identifier},
        )

    def is_loaded(self, obj: RideObjectInfo) -> bool:
        """Check whether an object is loaded in the current scenario."""
        try:
            self._client._query(
                "get_object",
                {"type": _object_type(obj), "identifier": obj.identifier},
            )
            return True
        except QueryError as e:
            if e.error == "not_loaded":
                return False
            raise

    def load(self, obj: RideObjectInfo) -> dict[str, Any]:
        """Load an object into the current scenario.

        This mutates the scenario's object table. The object stays loaded
        until explicitly unloaded or the scenario is reloaded.

        Returns the loaded object info (index, identifier, name, type).
        Raises RuntimeError if the object could not be loaded.
        """
        return self._client._query(
            "load_object",
            {"identifier": obj.identifier},
        )

    def unload(self, obj: RideObjectInfo) -> None:
        """Unload an object from the current scenario."""
        self._client._query(
            "unload_object",
            {"identifier": obj.identifier},
        )

    # ── Internal helpers ─────────────────────────────────────────────

    def _get_loaded_index(self, obj: RideObjectInfo) -> int | None:
        """Get the loaded object slot index, or None if not loaded."""
        try:
            result = self._client._query(
                "get_object",
                {"type": _object_type(obj), "identifier": obj.identifier},
            )
            return result["index"]
        except QueryError as e:
            if e.error == "not_loaded":
                return None
            raise

    def _require_loaded_index(self, obj: RideObjectInfo) -> int:
        """Get the loaded object slot index, raising if not loaded.

        Provides a clear error message directing the developer to load the object.
        """
        index = self._get_loaded_index(obj)
        if index is None:
            # TODO: Once we add const_name to RideObjectInfo via codegen,
            # include the exact RideObjects.category.CONST_NAME path here.
            raise RuntimeError(
                f"{obj.name} ({obj.identifier}) is not loaded in this scenario. Load it first with game.objects.load()."
            )
        return index


def _object_type(obj: RideObjectInfo) -> str:
    """Derive the bridge object type string from an object info instance.

    Currently all generated objects are rides. When we add SceneryObjectInfo etc.,
    this will dispatch on the class type.
    """
    # All RideObjectInfo instances are "ride" type (rides + stalls)
    return "ride"
