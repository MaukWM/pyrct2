"""Integration tests for game.park.staff high-level API.

Fixture state: empty park, no staff.
"""

import pytest

from pyrct2._generated.enums import StaffType

STAFF_TYPES = [StaffType.HANDYMAN, StaffType.MECHANIC, StaffType.SECURITY, StaffType.ENTERTAINER]


def test_list_empty(game):
    assert game.park.staff.list() == []


@pytest.mark.parametrize("staff_type", STAFF_TYPES, ids=[t.name for t in STAFF_TYPES])
def test_hire(game, staff_type):
    staff = game.park.staff.hire(staff_type)
    assert staff.data.staffType == staff_type.name.lower()


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
