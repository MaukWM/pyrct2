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
