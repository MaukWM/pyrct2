"""Shared fixtures for pyrct2 integration tests."""

import pytest

from pyrct2.client import RCT2

from pyrct2.scenarios import Scenario

TEST_SCENARIO = Scenario.TEST_PARK
TEST_SCENARIO_WITH_GUESTS = Scenario.TEST_PARK_WITH_GUESTS


@pytest.fixture
def game():
    """Launch a fresh game instance per test."""
    with RCT2.launch(TEST_SCENARIO) as g:
        yield g


@pytest.fixture
def game_with_guests():
    """Launch a game with 12 guests already in the park."""
    with RCT2.launch(TEST_SCENARIO_WITH_GUESTS) as g:
        yield g
