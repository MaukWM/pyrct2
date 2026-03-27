"""Integration tests for game.park.climate high-level API."""


def test_weather(game):
    _ = game.park.climate.weather


def test_temperature(game):
    _ = game.park.climate.temperature


def test_future(game):
    _ = game.park.climate.future


def test_force_weather_changes_climate(game):
    from pyrct2.park._climate import WeatherType

    game.park.cheats.force_weather(5)  # thunder
    assert game.park.climate.weather == WeatherType.THUNDER
