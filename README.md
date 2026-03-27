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
from pyrct2.scenarios import Scenario
from pyrct2.enums import ResearchFundingLevel, ResearchCategory

with RCT2.launch(Scenario.CRAZY_CASTLE) as game:
    # high-level API — read properties, call methods
    print(f"{game.park.name}: rating {game.park.rating}, cash ${game.park.finance.cash}")

    game.park.finance.set_entrance_fee(50)
    game.park.cheats.sandbox_mode()
    game.park.research.set_funding(ResearchFundingLevel.MAXIMUM)
    game.park.research.set_priorities([ResearchCategory.ROLLERCOASTER, ResearchCategory.THRILL])

    # tick-step the simulation forward
    game.advance_ticks(100)
    print(f"Weather: {game.park.climate.weather}")

    # raw API always available as escape hatch
    game.actions.staff_hire_new(auto_position=True, staff_type=0, costume_index=0, staff_orders=0)
    park = game.state.park()  # full Pydantic model
```

```python
# or attach to an already-running instance
with RCT2.connect() as game:
    print(game.park.name)
```

## Requirements

- Python 3.13+
- [OpenRCT2](https://openrct2.io/) installed with RCT2 game data
