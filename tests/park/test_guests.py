"""Integration tests for game.park.guests high-level API.

Uses test_scenario_with_guests fixture (12 guests, 10x10 map).
"""


def test_list(game_with_guests):
    guests = game_with_guests.park.guests.list()
    assert len(guests) == 12


def test_count(game_with_guests):
    assert game_with_guests.park.guests.count() == 12


def test_get(game_with_guests):
    guest = game_with_guests.park.guests.list()[0]
    assert game_with_guests.park.guests.get(guest.data.id) is not None
    assert game_with_guests.park.guests.get(9999) is None


def test_guest_entity_refresh(game_with_guests):
    """Guest entity data is stale after move_to, refresh() updates it."""
    from pyrct2.world import Tile

    guest = game_with_guests.park.guests.list()[0]
    old_tile = guest.tile

    guest.move_to(Tile(5, 5))

    # Data is stale — still shows old position
    assert guest.tile == old_tile

    guest.refresh()

    # Now it's updated
    assert guest.tile == Tile(5, 5)


def test_guest_move_to(game_with_guests):
    """Move a guest to different tiles."""
    from pyrct2.world import Tile

    guest = game_with_guests.park.guests.list()[0]
    guest.move_to(Tile(3, 3))
    guest.refresh()
    assert guest.tile == Tile(3, 3)

    guest.move_to(Tile(4, 4))
    guest.refresh()
    assert guest.tile == Tile(4, 4)
