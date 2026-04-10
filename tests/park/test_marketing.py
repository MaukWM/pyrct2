"""Integration tests for game.park.marketing campaigns."""

import pytest

from pyrct2._generated.enums import AdvertisingCampaignType, ShopItem
from pyrct2._generated.objects import RideObjects
from pyrct2.world import Tile


def test_campaign_park_wide(game):
    """Park-wide campaign succeeds with expected cost."""
    game.park.cheats.sandbox_mode()
    r = game.park.marketing.run_campaign(AdvertisingCampaignType.PARK, weeks=2)
    assert r.cost == 7000  # $3500/week * 2


def test_campaign_ride(game):
    """RIDE campaign targets a ride entity."""
    game.park.cheats.build_in_pause_mode()
    game.park.cheats.sandbox_mode()
    ride = game.rides.place_flat_ride(
        obj=RideObjects.gentle.MERRY_GO_ROUND,
        tile=Tile(20, 20),
        entrance=Tile(20, 22),
        exit=Tile(20, 18),
    )
    r = game.park.marketing.run_campaign(AdvertisingCampaignType.RIDE, weeks=1, ride=ride)
    assert r.cost == 2000


def test_campaign_ride_free_stall(game):
    """RIDE_FREE campaign works on a stall."""
    game.park.cheats.build_in_pause_mode()
    game.park.cheats.sandbox_mode()
    stall = game.rides.place_stall(RideObjects.stall.BURGER_BAR, Tile(20, 20))
    r = game.park.marketing.run_campaign(AdvertisingCampaignType.RIDE_FREE, weeks=1, ride=stall)
    assert r.cost == 500


def test_campaign_food_free(game):
    """FOOD_OR_DRINK_FREE campaign with ShopItem."""
    game.park.cheats.sandbox_mode()
    r = game.park.marketing.run_campaign(
        AdvertisingCampaignType.FOOD_OR_DRINK_FREE,
        weeks=3,
        shop_item=ShopItem.BURGER,
    )
    assert r.cost == 1500  # $500/week * 3


def test_campaign_ride_missing_target(game):
    """RIDE campaign without ride= raises ValueError."""
    with pytest.raises(ValueError, match="requires a ride="):
        game.park.marketing.run_campaign(AdvertisingCampaignType.RIDE, weeks=1)


def test_campaign_food_missing_target(game):
    """FOOD_OR_DRINK_FREE without shop_item= raises ValueError."""
    with pytest.raises(ValueError, match="requires a shop_item="):
        game.park.marketing.run_campaign(AdvertisingCampaignType.FOOD_OR_DRINK_FREE, weeks=1)


def test_campaign_park_wide_rejects_targets(game):
    """Park-wide campaign with ride= raises ValueError."""
    with pytest.raises(ValueError, match="does not take"):
        game.park.marketing.run_campaign(AdvertisingCampaignType.PARK, weeks=1, ride=0)
