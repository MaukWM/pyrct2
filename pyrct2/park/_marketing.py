"""MarketingProxy — advertising campaign management.

TODO: Add active campaign query. The plugin API has no way to read active campaigns.
Options: (1) bridge-side hook tracking on parkmarketing action execution,
or (2) upstream PR to expose park.marketingCampaigns to the scripting layer.
Once available, add list_active() and verify campaigns in tests.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyrct2._generated.enums import AdvertisingCampaignType, ShopItem
from pyrct2.result import ActionResult

if TYPE_CHECKING:
    from pyrct2.client import RCT2
    from pyrct2.park._rides import RideEntity

# Campaign types that require a ride/stall target.
_RIDE_CAMPAIGNS = {AdvertisingCampaignType.RIDE, AdvertisingCampaignType.RIDE_FREE}
# Campaign type that requires a shop item target.
_SHOP_ITEM_CAMPAIGN = AdvertisingCampaignType.FOOD_OR_DRINK_FREE


class MarketingProxy:
    """Marketing campaigns: ``game.park.marketing``."""

    def __init__(self, client: RCT2) -> None:
        self._client = client

    def run_campaign(
        self,
        campaign: AdvertisingCampaignType,
        weeks: int,
        *,
        ride: RideEntity | int | None = None,
        shop_item: ShopItem | None = None,
    ) -> ActionResult:
        """Start a marketing campaign.

        Args:
            campaign: The campaign type.
            weeks: Duration in weeks (1-255). The game UI caps at 6
                but the engine accepts up to 255.
            ride: Target ride or stall for RIDE / RIDE_FREE campaigns.
                Accepts a RideEntity or raw ride ID.
            shop_item: Target item for FOOD_OR_DRINK_FREE campaigns
                (e.g. ``ShopItem.BURGER``).

        Raises:
            ValueError: If a required target is missing or an unexpected
                target is provided for the campaign type.
        """
        if campaign in _RIDE_CAMPAIGNS:
            if ride is None:
                raise ValueError(f"{campaign.name} requires a ride=target")
            item = ride if isinstance(ride, int) else ride.data.id
        elif campaign == _SHOP_ITEM_CAMPAIGN:
            if shop_item is None:
                raise ValueError(f"{campaign.name} requires a shop_item=target")
            item = int(shop_item)
        else:
            if ride is not None or shop_item is not None:
                raise ValueError(f"{campaign.name} is park-wide and does not take ride= or shop_item=")
            item = 0

        return ActionResult.from_response(
            self._client.actions.park_marketing(
                type=campaign,
                item=item,
                duration=weeks,
            )
        )
