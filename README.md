# pyrct2

Python client for [OpenRCT2](https://openrct2.io/). Launch headless games, read state, execute actions, all in Python!

Connects to the [openrct2-bridge](https://github.com/MaukWM/openrct2-bridge) plugin over TCP. Every game action, state query, and enum is auto-generated from [OpenRCT2 C++ source](https://github.com/OpenRCT2/OpenRCT2) by [openrct2-codegen](https://github.com/MaukWM/openrct2-actiongen).

## Install

```bash
pip install pyrct2
pyrct2 setup        # finds OpenRCT2, installs the bridge plugin
```

## Usage

```python
from pyrct2.client import RCT2
from pyrct2.enums import StaffType, AdvertisingCampaignType, ResearchFundingLevel

with RCT2.launch("/path/to/Scenarios/Crazy Castle.SC6") as game:
    # state queries return typed Pydantic models
    park = game.state.park()
    print(f"{park.name}: rating {park.rating}, cash ${park.cash}")

    # actions take typed enums — no magic ints
    game.actions.staff_hire_new(auto_position=True, staff_type=StaffType.MECHANIC, costume_index=0, staff_orders=0)
    game.actions.park_marketing(type=AdvertisingCampaignType.PARK_ENTRY_FREE, item=0, duration=4)
    game.actions.park_set_research_funding(priorities=0xFF, funding_amount=ResearchFundingLevel.MAXIMUM)

    # tick-step the simulation forward
    game.advance_ticks(100)
    print(f"Rating: {game.state.park_rating()}")
```

```python
# or attach to an already-running instance
with RCT2.connect() as game:
    print(game.state.scenario_name())
```

## Requirements

- Python 3.13+
- [OpenRCT2](https://openrct2.io/) installed with RCT2 game data
