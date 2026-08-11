This project has been created as part of the 42 curriculum by haer-reh

Fly-in — Drone Pathfinding & Visualization Simulator
===================================================

Description
-------
Fly-in is a drone routing simulator that parses a simple map/config
format, computes shortest/feasible paths for multiple drones using a
constrained Dijkstra-based planner, schedules turn-by-turn moves while
respecting hub capacities and link capacities, and renders an animated
visualization with pygame.

Features
--------
- Text-based configuration format: define number of drones, start/end hubs,
  intermediate hubs and connections.
- Pathfinding: Dijkstra over an undirected graph with zone-based costs.
- Turn scheduling: per-turn movement simulation accounting for hub capacity,
  link capacity, transit delays for restricted zones, and dynamic replanning.
- Visualization: smooth, zoomable pygame view with occupancy badges and
  animated drone icons. Optional image assets supported.

Instructions
----------
1. Install dependencies (Python 3.10+):

```bash
make install
```

2. Run the simulator using the included example map (located at src/map.txt):

```bash
make run
```

Behavior
--------
- The program parses the config file and validates prefixes `nb_drones:`,
  `start_hub:`, `end_hub:`, `hub:`, and `connection:`.
- After parsing, the engine builds an adjacency graph and runs Dijkstra to
  compute a cheapest path from start to end. Zone types influence cost:
  `normal`/`priority` = 1, `restricted` = 2 (blocked zones are omitted).
- The turn scheduler advances drones turn-by-turn while enforcing hub
  capacity (`max_drones`) and connection capacity (`max_link_capacity`). If a
  path becomes blocked, a drone will attempt to re-plan using the current
  occupancy state.
- The visualizer animates drone movement and prints connection occupancy per
  turn to stdout; it also supports optional assets/Drone.png and
  assets/Background.png for custom visuals.

Configuration format (example)
------------------------------
The example src/map.txt demonstrates the format. Key lines:

- `nb_drones: N` — number of drones to simulate.
- `start_hub: NAME X Y [meta]` — starting hub name and coordinates.
- `end_hub: NAME X Y [meta]` — destination hub name and coordinates.
- `hub: NAME X Y [meta]` — intermediate hub. `meta` (optional) uses
  `color=NAME`, `max_drones=N`, `zone=<normal|restricted|blocked|priority>`.
- `connection: A-B [meta]` — undirected connection between hubs A and B.
  Optional meta: `max_link_capacity=N`.

See src/map.txt for a non-trivial sample containing multiple hub zones,
dead-ends, and varied capacities.

Project layout
--------------
- `pyproject.toml` — package metadata and dependency hints (pygame, pydantic).
- `src/__main__.py` — entry point that runs parser → simulation → visualizer.
- `src/parser.py` — reads and validates the config text.
- `src/config_maker.py` — translates parsed lines into typed objects and
  validates graph connectivity and duplicates.
- `src/objects.py` — data models for `hub`, `connection`, `drone`, `start_hub`,
  and `end_hub`.
- `src/simulation_engine.py` — pathfinding (`dijkstra_once`) and turn
  scheduling (`turn_scheduler`).
- `src/visualizer.py` & `src/vis_utils.py` — pygame renderer, UI helpers and
  constants.
- `src/parser_helpers.py` — small metadata parsing helpers.

Algorithm notes
---------------
- Pathfinding: standard Dijkstra using a min-heap. Node costs include a base
  per-zone multiplier to represent restricted zones increasing transit time.
- Scheduling: simulation advances in discrete turns. Drones occupying a
  connection or waiting for space are tracked, and the engine will re-plan
  paths for drones when blocked by capacity constraints. End hubs and start
  hubs are treated as having effectively infinite capacity.

Dependencies
------------
- Python >= 3.10
- pygame >= 2.6.1
- pydantic >= 2.13.4

Resources
-----------

https://www.youtube.com/watch?v=bZkzH5x0SKU

https://cp-algorithms.com/graph/dijkstra.html

https://pygame.readthedocs.io/en/latest/1_intro/intro.html

https://www.youtube.com/watch?v=EFg3u_E6eHU


AI usage
----------------
simplifying docs and closing knowledge gaps for various topics, including pygame, dijkstra.
adding docstrings to functions and classes, and providing explanations for complex logic.
fixing mypy and flake8 errors.
generating custom test cases for the simulation engine and visualizer.
 