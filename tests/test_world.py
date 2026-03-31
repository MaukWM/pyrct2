"""Integration tests for game.world proxy.

Tests run against both fixture parks:
- test_scenario.park: 52x52, flat, owned, surface-only tiles
- test_scenario_with_guests.park: 12x12, has footpaths and park entrance
"""

from pyrct2.world import Tile, TileData


# ── get_bounds ────────────────────────────────────────────────────────


def test_get_bounds(game):
    bounds = game.world.get_bounds()
    assert bounds.x == 52
    assert bounds.y == 52


def test_get_bounds_with_guests(game_with_guests):
    bounds = game_with_guests.world.get_bounds()
    assert bounds.x == 12
    assert bounds.y == 12


# ── get_tile ──────────────────────────────────────────────────────────


def test_get_tile_returns_tile_data(game):
    tile = game.world.get_tile(Tile(x=26, y=26))
    assert tile.x == 26
    assert tile.y == 26


def test_get_tile_surface(game):
    """Every tile has a .surface property."""
    tile = game.world.get_tile(Tile(x=26, y=26))
    assert tile.surface.hasOwnership is True


def test_get_tile_edge_unowned(game):
    """Edge tile (0,0) is not owned."""
    tile = game.world.get_tile(Tile(x=0, y=0))
    assert tile.surface.hasOwnership is False


def test_get_tile_with_footpath(game_with_guests):
    """Tile (5,5) in guest park has a footpath."""
    tile = game_with_guests.world.get_tile(Tile(x=5, y=5))
    assert len(tile.paths) == 1


def test_get_tile_with_entrance(game_with_guests):
    """Tile (9,5) in guest park has a park entrance."""
    tile = game_with_guests.world.get_tile(Tile(x=9, y=5))
    assert len(tile.entrances) == 1


def test_get_tile_empty_lists(game):
    """Surface-only tile has empty lists for other element types."""
    tile = game.world.get_tile(Tile(x=26, y=26))
    assert tile.paths == []
    assert tile.tracks == []
    assert tile.scenery == []
    assert tile.walls == []
    assert tile.entrances == []
    assert tile.banners == []


# ── get_tiles (batch) ─────────────────────────────────────────────────


def test_get_tiles_returns_tile_data(game):
    """Batch returns list of TileData."""
    tiles = game.world.get_tiles(Tile(x=25, y=25), Tile(x=27, y=27))
    assert len(tiles) == 9
    assert all(isinstance(t, TileData) for t in tiles)


def test_get_tiles_matches_individual(game):
    """Batch result matches individual get_tile calls."""
    batch = game.world.get_tiles(Tile(x=25, y=25), Tile(x=26, y=26))
    for tile_data in batch:
        individual = game.world.get_tile(Tile(x=tile_data.x, y=tile_data.y))
        assert tile_data == individual


def test_get_tiles_with_footpaths(game_with_guests):
    """Batch across path area returns tiles with footpaths."""
    tiles = game_with_guests.world.get_tiles(Tile(x=4, y=5), Tile(x=8, y=5))
    assert len(tiles) == 5
    for tile in tiles:
        assert len(tile.paths) == 1
