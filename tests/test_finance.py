"""Integration tests for game.park.finance high-level API.

Fixture state: cash=500000, loan=100000, max_loan=500000, entrance_fee=100.
"""


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
