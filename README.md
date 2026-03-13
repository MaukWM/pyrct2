# pyrct2

Python client for OpenRCT2. Launches the game in headless mode, connects to the [openrct2-bridge](https://github.com/MaukWM/openrct2-bridge) plugin over TCP, and sends game actions.

## Setup

```bash
pip install pyrct2
pyrct2 setup
```

`setup` finds your OpenRCT2 installation and installs the bridge plugin. Requires [OpenRCT2](https://openrct2.io/) to be installed.

## Usage

```python
from pyrct2.client import RCT2

# Launch a headless game and send commands
with RCT2.launch("path/to/scenario.SC6") as game:
    game.get_status()
    game.execute("ridecreate", {"rideType": 1, "rideObject": 0, "colour1": 5, "colour2": 10})
    game.advance_ticks(100)

# Or connect to an already-running instance
with RCT2.connect() as game:
    game.get_status()
```
