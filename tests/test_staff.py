"""Integration tests for game.park.staff high-level API.

Fixture state: empty park, no staff.
"""
from pyrct2._generated.enums import Colour, StaffType

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
