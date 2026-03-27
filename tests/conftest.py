"""Shared fixtures for pyrct2 integration tests."""

from pathlib import Path

import pytest

from pyrct2.client import RCT2

FIXTURES_DIR = Path(__file__).parent / "fixtures"
TEST_SCENARIO = FIXTURES_DIR / "test_scenario.park"


@pytest.fixture
def game():
    """Launch a fresh game instance per test."""
    with RCT2.launch(TEST_SCENARIO) as g:
        yield g
