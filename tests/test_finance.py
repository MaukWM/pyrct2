"""Integration tests for game.park.finance high-level API.

Fixture state: cash=500000, loan=100000, max_loan=500000, entrance_fee=100.
"""

import pytest

from pyrct2.errors import ActionError


def test_cash(game):
    assert game.park.finance.cash == 500000


def test_loan(game):
    assert game.park.finance.loan == 100000


def test_max_loan(game):
    assert game.park.finance.max_loan == 500000


def test_entrance_fee(game):
    assert game.park.finance.entrance_fee == 100


def test_set_entrance_fee(game):
    game.park.finance.set_entrance_fee(250)
    assert game.park.finance.entrance_fee == 250


def test_set_loan(game):
    game.park.finance.set_loan(200000)
    assert game.park.finance.loan == 200000


def test_take_loan(game):
    game.park.finance.take_loan(50000)
    assert game.park.finance.loan == 150000


def test_repay_loan(game):
    game.park.finance.repay_loan(50000)
    assert game.park.finance.loan == 50000


# -- Error cases --


def test_negative_loan_raises(game):
    with pytest.raises(ActionError):
        game.park.finance.set_loan(-100)
    assert game.park.finance.loan == 100000  # unchanged


def test_loan_above_max_raises(game):
    with pytest.raises(ActionError):
        game.park.finance.set_loan(999999999)
    assert game.park.finance.loan == 100000  # unchanged


def test_take_loan_above_max_raises(game):
    with pytest.raises(ActionError):
        game.park.finance.take_loan(999999999)
    assert game.park.finance.loan == 100000  # unchanged


def test_repay_more_than_owed_raises(game):
    with pytest.raises(ActionError):
        game.park.finance.repay_loan(999999999)
    assert game.park.finance.loan == 100000  # unchanged


def test_negative_entrance_fee_raises(game):
    with pytest.raises(ActionError):
        game.park.finance.set_entrance_fee(-50)
    assert game.park.finance.entrance_fee == 100  # unchanged
