"""PeepEntity base class and shared peep helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyrct2._entity import EntityBase
from pyrct2._generated.enums import PeepPickupType
from pyrct2.world._tile import TILE_SIZE, Tile

if TYPE_CHECKING:
    from pyrct2.client import RCT2


class PeepEntity(EntityBase):
    """Base for peep entities (guests, staff).

    All peeps have a world position (x, y, z) and can be picked up and moved.
    """

    @property
    def tile(self) -> Tile:
        """Tile this peep is standing on (floored from world coords)."""
        return Tile.from_world(self.data.x, self.data.y)

    def move_to(self, tile: Tile, height: int | None = None) -> None:
        """Pick up this peep and place them on the target tile.

        Args:
            tile: Destination tile.
            height: Height in land steps. If None, places at surface height.

        Raises:
            ValueError: If height is below the tile's surface.
        """
        z = self._client.world.resolve_height(tile, height)
        _peep_move(self._client, self._id, tile, z)


def _peep_move(client: RCT2, entity_id: int, tile: Tile, z: int) -> None:
    """Cancel any prior pickup state, then pick up and place a peep.

    The game leaves an internal "just placed" flag after PLACE that causes
    the next PICKUP+PLACE to fail with "Can't place person here." A CANCEL
    before PICKUP clears this (and is harmless if there's nothing to cancel).

    If PLACE fails, the peep is cancelled back to their original position
    so they don't get stranded at x=-32768 (the picked-up sentinel).
    CANCEL's x/y/z params control where the peep lands.

    player_id=0: hardcoded for single-player; multiplayer not supported.
    """
    _base = {"id": entity_id, "x": 0, "y": 0, "z": 0, "player_id": 0}

    # Clear any leftover pickup state from a previous move or a crashed move.
    # Without this, a second PICKUP+PLACE fails (see openrct2-api-bugs.md #9).
    client.actions.peep_pickup(type=PeepPickupType.CANCEL, **_base)

    # PICKUP returns the peep's position — save it for rollback on failure.
    result = client.actions.peep_pickup(type=PeepPickupType.PICKUP, **_base)
    origin = result["payload"]["position"]

    try:
        client.actions.peep_pickup(
            type=PeepPickupType.PLACE,
            id=entity_id,
            x=tile.x * TILE_SIZE,
            y=tile.y * TILE_SIZE,
            z=z,
            player_id=0,
        )
    except Exception:
        # Place failed — cancel back to original position.
        client.actions.peep_pickup(
            type=PeepPickupType.CANCEL,
            id=entity_id,
            x=origin["x"],
            y=origin["y"],
            z=origin["z"],
            player_id=0,
        )
        raise
