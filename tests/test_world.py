"""Integration tests for game.world proxy.

Tests run against both fixture parks:
- test_scenario.park: 52x52, flat, owned, surface-only tiles
- test_scenario_with_guests.park: 12x12, has footpaths and park entrance
"""

from pyrct2.world import SLOPE_N, Tile, TileData


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


def test_corner_heights_flat(game):
    """Flat tile has equal corner heights."""
    tile = game.world.get_tile(Tile(x=26, y=26))
    assert tile.corner_heights.is_flat


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


# ── Area queries ──────────────────────────────────────────────────────


def test_max_corner_height(game):
    """Flat area returns consistent max height."""
    h = game.world.max_corner_height(Tile(x=25, y=25), Tile(x=27, y=27))
    single = game.world.get_tile(Tile(x=26, y=26)).corner_heights.max
    assert h == single


def test_is_area_flat(game):
    """Center of test park is flat."""
    assert game.world.is_area_flat(Tile(x=25, y=25), Tile(x=27, y=27))


# ── Terraform ─────────────────────────────────────────────────────────


def test_set_height(game):
    """Set exact height in land steps."""
    game.park.cheats.build_in_pause_mode()
    game.world.set_height(Tile(x=20, y=20), height=10)
    tile = game.world.get_tile(Tile(x=20, y=20))
    assert tile.corner_heights.max == 10
    assert tile.corner_heights.is_flat


def test_set_height_with_slope(game):
    """Set height with N corner raised."""
    game.park.cheats.build_in_pause_mode()
    game.world.set_height(Tile(x=20, y=20), height=10, slope=SLOPE_N)
    tile = game.world.get_tile(Tile(x=20, y=20))
    assert not tile.corner_heights.is_flat
    assert tile.corner_heights.n == 11
    assert tile.corner_heights.s == 10


def test_raise_land(game):
    """Raise increases height by one land step."""
    game.park.cheats.build_in_pause_mode()
    before = game.world.get_tile(Tile(x=20, y=20)).corner_heights.max
    game.world.raise_land(Tile(x=20, y=20))
    after = game.world.get_tile(Tile(x=20, y=20)).corner_heights.max
    assert after == before + 1


def test_lower_land(game):
    """Lower decreases height by one land step."""
    game.park.cheats.build_in_pause_mode()
    before = game.world.get_tile(Tile(x=20, y=20)).corner_heights.max
    game.world.lower_land(Tile(x=20, y=20))
    after = game.world.get_tile(Tile(x=20, y=20)).corner_heights.max
    assert after == before - 1


def test_is_area_flat_after_raise(game):
    """Flat area → raise one tile → no longer flat."""
    game.park.cheats.build_in_pause_mode()
    area = (Tile(x=20, y=20), Tile(x=22, y=22))
    assert game.world.is_area_flat(*area)
    game.world.raise_land(Tile(x=21, y=21))
    assert not game.world.is_area_flat(*area)


def test_max_corner_height_after_raise(game):
    """Max height increases after raising part of the area."""
    game.park.cheats.build_in_pause_mode()
    area = (Tile(x=20, y=20), Tile(x=22, y=22))
    before = game.world.max_corner_height(*area)
    game.world.raise_land(Tile(x=21, y=21))
    after = game.world.max_corner_height(*area)
    assert after == before + 1


def test_raise_land_smooth_affects_neighbors(game):
    """Smooth raise creates slopes on surrounding tiles."""
    game.park.cheats.build_in_pause_mode()
    center = Tile(x=30, y=30)

    # Verify area is flat before
    assert game.world.is_area_flat(Tile(x=29, y=29), Tile(x=31, y=31))

    game.world.raise_land_smooth(center)

    # Center should be raised
    assert game.world.get_tile(center).corner_heights.max > game.world.get_tile(Tile(x=25, y=25)).corner_heights.max

    # At least some neighbors should now be sloped (not flat)
    neighbors_sloped = 0
    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        tile = game.world.get_tile(Tile(x=30 + dx, y=30 + dy))
        if not tile.corner_heights.is_flat:
            neighbors_sloped += 1
    assert neighbors_sloped > 0, "Smooth raise should create slopes on neighbors"
