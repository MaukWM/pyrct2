"""Integration tests for game.paths high-level API."""

from pyrct2.world._tile import Tile


def test_place_path(game):
    game.park.cheats.build_in_pause_mode()
    result = game.paths.place(Tile(10, 10))
    assert result.cost > 0

    tile = game.world.get_tile(Tile(10, 10))
    assert len(tile.paths) == 1


def test_place_path_auto_connects(game):
    """Place a 2x2 square and verify all edges connect correctly.

    Layout:        Edge bits: bit0=W, bit1=S, bit2=E, bit3=N
      NW  NE
      SW  SE
    """
    game.park.cheats.build_in_pause_mode()
    # NW, NE, SW, SE
    game.paths.place(Tile(10, 10))
    game.paths.place(Tile(11, 10))
    game.paths.place(Tile(10, 11))
    game.paths.place(Tile(11, 11))

    nw = game.world.get_tile(Tile(10, 10)).paths[0].edges
    ne = game.world.get_tile(Tile(11, 10)).paths[0].edges
    sw = game.world.get_tile(Tile(10, 11)).paths[0].edges
    se = game.world.get_tile(Tile(11, 11)).paths[0].edges

    # NW: east + south
    assert nw & 0b0100, "NW should have east edge"
    assert nw & 0b0010, "NW should have south edge"
    # NE: west + south
    assert ne & 0b0001, "NE should have west edge"
    assert ne & 0b0010, "NE should have south edge"
    # SW: east + north
    assert sw & 0b0100, "SW should have east edge"
    assert sw & 0b1000, "SW should have north edge"
    # SE: west + north
    assert se & 0b0001, "SE should have west edge"
    assert se & 0b1000, "SE should have north edge"


def test_place_queue_path(game):
    game.park.cheats.build_in_pause_mode()
    game.paths.place(Tile(10, 10), queue=True)

    path = game.world.get_tile(Tile(10, 10)).paths[0]
    assert path.isQueue is True
