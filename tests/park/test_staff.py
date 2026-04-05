"""Integration tests for game.park.staff high-level API.

Fixture state: empty park, no staff.
"""

from pyrct2._generated.enums import Colour, StaffType
from pyrct2.world import Tile

STAFF_TYPES = [StaffType.HANDYMAN, StaffType.MECHANIC, StaffType.SECURITY, StaffType.ENTERTAINER]


def test_list_empty(game):
    assert game.park.staff.list() == []


def test_hire_all_types(game):
    for staff_type in STAFF_TYPES:
        game.park.staff.hire(staff_type)
    staff = game.park.staff.list()
    assert len(staff) == 4
    types = {s.data.staffType for s in staff}
    assert types == {"handyman", "mechanic", "security", "entertainer"}


def test_get(game):
    hired = game.park.staff.hire(StaffType.HANDYMAN)
    assert game.park.staff.get(hired.data.id) is not None
    assert game.park.staff.get(9999) is None


def test_rename(game):
    staff = game.park.staff.hire(StaffType.HANDYMAN)
    staff.rename("Bob")
    assert game.park.staff.get(staff.data.id).data.name == "Bob"


def test_staff_entity_refresh(game):
    """Staff entity data is stale after write, refresh() updates it."""
    staff = game.park.staff.hire(StaffType.HANDYMAN)
    old_name = staff.data.name

    staff.rename("Refreshed Bob")

    # Data is stale
    assert staff.data.name == old_name

    staff.refresh()

    # Now it's updated
    assert staff.data.name == "Refreshed Bob"


def test_fire(game):
    staff = game.park.staff.hire(StaffType.HANDYMAN)
    entity_id = staff.data.id
    staff.fire()
    assert game.park.staff.get(entity_id) is None


def test_set_colour(game):
    staff = game.park.staff.hire(StaffType.HANDYMAN)
    staff.set_colour(Colour.BRIGHT_RED)
    refreshed = game.park.staff.get(staff.data.id)
    assert refreshed.data.colour == Colour.BRIGHT_RED


def test_staff_move_to(game):
    """Move a staff member to different tiles."""
    staff = game.park.staff.hire(StaffType.HANDYMAN)
    staff.move_to(Tile(5, 5))
    staff.refresh()
    assert staff.tile == Tile(5, 5)

    staff.move_to(Tile(6, 6))
    staff.refresh()
    assert staff.tile == Tile(6, 6)


def test_set_patrol_area(game):
    """set_patrol replaces the entire patrol area."""
    staff = game.park.staff.hire(StaffType.HANDYMAN)
    staff.set_patrol_area(Tile(x=5, y=5), Tile(x=6, y=6))
    refreshed = game.park.staff.get(staff.data.id)
    assert len(refreshed.patrol_tiles) == 4

    # set_patrol replaces — should be 9, not 13
    refreshed.set_patrol_area(Tile(x=10, y=10), Tile(x=12, y=12))
    refreshed2 = game.park.staff.get(staff.data.id)
    assert len(refreshed2.patrol_tiles) == 9


def test_add_patrol_area(game):
    """add_patrol is additive."""
    staff = game.park.staff.hire(StaffType.HANDYMAN)
    staff.add_patrol_area(Tile(x=5, y=5), Tile(x=6, y=6))
    staff.add_patrol_area(Tile(x=10, y=10), Tile(x=11, y=11))
    refreshed = game.park.staff.get(staff.data.id)
    assert len(refreshed.patrol_tiles) == 8  # 4 + 4


def test_remove_patrol_area(game):
    """remove_patrol removes tiles from the area."""
    staff = game.park.staff.hire(StaffType.HANDYMAN)
    staff.set_patrol_area(Tile(x=5, y=5), Tile(x=8, y=8))
    refreshed = game.park.staff.get(staff.data.id)
    assert len(refreshed.patrol_tiles) == 16

    refreshed.remove_patrol_area(Tile(x=7, y=7), Tile(x=8, y=8))
    refreshed2 = game.park.staff.get(staff.data.id)
    assert len(refreshed2.patrol_tiles) == 12


def test_clear_patrol_area(game):
    staff = game.park.staff.hire(StaffType.HANDYMAN)
    staff.set_patrol_area(Tile(x=5, y=5), Tile(x=8, y=8))
    refreshed = game.park.staff.get(staff.data.id)
    assert len(refreshed.patrol_tiles) == 16

    refreshed.clear_patrol_area()
    refreshed2 = game.park.staff.get(staff.data.id)
    assert refreshed2.patrol_tiles == []
