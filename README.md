# pyrct2

Python client for [OpenRCT2](https://openrct2.io/). Launch headless games, read state, execute actions, all in Python!

Connects to the [openrct2-bridge](https://github.com/MaukWM/openrct2-bridge) plugin over TCP. Every game action, state query, and enum is auto-generated from [OpenRCT2 C++ source](https://github.com/OpenRCT2/OpenRCT2) by [openrct2-codegen](https://github.com/MaukWM/openrct2-actiongen).

## Install

```bash
pip install pyrct2
pyrct2 setup        # finds OpenRCT2, installs the bridge plugin
```

## Quick start

```python
from pyrct2.client import RCT2
from pyrct2.scenarios import Scenario

# Launch a built-in scenario
with RCT2.launch(Scenario.TEST_PARK) as game:
    print(f"{game.park.name}: rating {game.park.rating}, cash ${game.park.finance.cash}")

# Or load a scenario/save by path
with RCT2.launch("/path/to/my_park.park") as game:
    print(game.park.name)

# Or connect to an already-running instance
with RCT2.connect() as game:
    print(game.park.name)
```


## Building a park

```python
from pyrct2.client import RCT2
from pyrct2.enums import Direction, StaffType
from pyrct2.objects import RideObjects, FootpathAdditions, FootpathSurfaces, FootpathRailings
from pyrct2.scenarios import Scenario
from pyrct2.world import Tile

with RCT2.launch(Scenario.CRAZY_CASTLE, headless=False) as game:
    game.park.cheats.build_in_pause_mode()
    game.park.finance.set_entrance_fee(10)

    # -- Match the scenario's path style --
    game.paths.set_default_surface(FootpathSurfaces.TARMAC)

    # -- Place a flat ride south of the main path --
    ride = game.rides.place_flat_ride(
        obj=RideObjects.gentle.MERRY_GO_ROUND,
        tile=Tile(44, 34),
        entrance=Tile(44, 32),
        exit=Tile(46, 34),
        direction=Direction.NORTH,
    )
    ride.set_price(30)
    ride.open()

    # -- Place some stalls along the main path --
    burger = game.rides.place_stall(RideObjects.stall.BURGER_BAR, Tile(42, 29))
    burger.open()
    drink = game.rides.place_stall(RideObjects.stall.DRINKS_STALL, Tile(46, 29))
    drink.open()

    # -- Paths --
    game.paths.place_line(Tile(44, 30), Tile(44, 31))           # branch to ride
    game.paths.place(Tile(44, 31), queue=True)                   # queue to entrance
    game.paths.place_line(Tile(46, 30), Tile(46, 34))            # exit path back

    # path additions
    game.paths.place_addition(Tile(43, 30), FootpathAdditions.LAMP1)
    game.paths.place_addition(Tile(45, 30), FootpathAdditions.BENCH1)
    game.paths.place_addition(Tile(47, 30), FootpathAdditions.LITTER1)

    # verify connectivity from entrance to ride
    assert game.paths.is_connected(Tile(48, 30), Tile(44, 31))

    # -- Staff --
    handyman = game.park.staff.hire(StaffType.HANDYMAN)
    handyman.set_patrol_area(Tile(40, 28), Tile(50, 36))
    game.park.staff.hire(StaffType.MECHANIC)

    # -- Open the park and let it run --
    game.park.open()
    game.park.cheats.generate_guests(50)
    game.advance_ticks(100)

    # -- Read state --
    print(f"Rating: {game.park.rating}, Guests: {game.park.guests.count()}")
    print(f"Cash: {game.state.park().cash}")
    for r in game.state.rides():
        print(f"  {r.name}: {r.status}, excitement {r.excitement}")
```

## Raw API

All 82 game actions and state queries are available directly if you need something the high-level API doesn't wrap yet:

```python
# Actions (raw ints, less friendly)
game.actions.staff_hire_new(auto_position=True, staff_type=0, costume_index=0, staff_orders=0)
game.actions.ride_set_price(ride=0, price=50, is_primary_price=True)

# State queries (full Pydantic models)
game.state.date()                          # GameDate — ticks, day, month, year
game.state.scenario()                      # Scenario — objectives, completion status
game.state.climate()                       # Climate — current/future weather
game.state.park_messages()                 # list[ParkMessage] — guest complaints, awards
game.state.park_awards()                   # list[Award]
game.state.park_research()                 # Research — invented/uninvented items
game.state.guests()                        # list[Guest] — every guest in the park
```

## Requirements

- Python 3.11+
- [OpenRCT2](https://openrct2.io/) installed with RCT2 game data
