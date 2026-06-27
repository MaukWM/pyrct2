# pyrct2 Track Building Examples

Examples demonstrating how to build tracked rides programmatically.

All examples use `Scenario.TEST_PARK_LARGE` (256x256 flat map with ride objects
pre-loaded) and require `pyrct2 setup` to have been run first.

```bash
cd pyrct2 && uv run python examples/01_simple_oval.py
```

## Examples

| # | File | What it demonstrates |
|---|------|---------------------|
| 01 | `01_simple_oval.py` | Minimal flat oval circuit — the "hello world" of coaster building |
| 02 | `02_hill_coaster.py` | Chain lift climb with descent — slope transitions |
| 03 | `03_steep_coaster.py` | 60-degree slopes — steep transitions with brakes |
| 04 | `04_banked_turns.py` | Banked 5-tile sweeping turns — bank enter/exit pattern |
| 05 | `05_corkscrew_coaster.py` | Double corkscrew pairs — special piece chaining |
| 06 | `06_vertical_loop.py` | Vertical loop — enters from slope, exits at slope |
| 07 | `07_log_flume.py` | Log Flume water ride — same API, different ride type |
| 08 | `08_mini_railway.py` | Miniature Railway transport ride — large scenic loop |
| 09 | `09_wide_sweeping_turns.py` | 5-tile turns — compact circuit with wide corners |
| 10 | `10_using_valid_next.py` | Inspecting `.valid_next` before placing — agent decision making |
| 11 | `11_undo.py` | Removing pieces with `.undo()` — station protection |
| 12 | `12_on_ride_photo.py` | On-ride photo and brakes — special flat pieces |

## Circuit Geometry Cheat Sheet

For rectangular circuits with 3-tile turns (R3/L3) and `station_length=3`:

```
Formula: [n-2, m, n+1, m] flats per side
Example: n=5, m=5 → [3, 5, 6, 5]
```

For 5-tile turns (R5/L5) with `station_length=3`:

```
Formula: [0, m, m, m] (station fills side 0)
Example: m=3 → [0, 3, 3, 3]
```

Slope pieces count as 1 tile each (same horizontal advancement as flat).
