"""Shared fixtures for pyrct2 integration tests."""

from pathlib import Path

import pytest

from pyrct2.client import RCT2

FIXTURES_DIR = Path(__file__).parent / "fixtures"
TEST_SCENARIO = FIXTURES_DIR / "test_scenario.park"
TEST_SCENARIO_WITH_GUESTS = FIXTURES_DIR / "test_scenario_with_guests.park"


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
