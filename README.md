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

## Known Limitations

### Windows: Headless launch crashes on rapid succession

OpenRCT2's headless mode on Windows crashes approximately about 1 out of 3 times when launching and terminating instances in quick succession. Probably an issue with cleaning up and allocating space for the next game instance.  This might automatically resolve itself when port discovery/assignment is added.

Exit codes seen over a few trials:
- `3221356611` (`0xC0020043`) — `RPC_S_NO_INTERFACES`, COM/RPC resource cleanup failure
- `3221225620` (`0xC0000374`) — `STATUS_HEAP_CORRUPTION`, heap corruption during startup
- `3221226505` (`0xC0000409`) — `STATUS_STACK_BUFFER_OVERRUN`, stack buffer overrun
