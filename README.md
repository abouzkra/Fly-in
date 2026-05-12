*This project has been created as part of the 42 curriculum by abouzkra*

# Description
**Fly-in** is a drone fleet routing simulation written in Python. The goal is to move all drones from a central start hub to a target end hub across a network of connected zones, in the fewest possible simulation turns.
The program reads a custom map file that defines zones, connections, capacities and zone types, then computes a routing plan and visualises the simulation using **Raylib**.
The project is split into four independent layers:

- **Parsing** — reads the map file format and builds an in-memory model, enforcing all syntactic and semantic constraints.
- **Graph** — constructs a directed weighted graph from the parsed map, encoding zone types as movement costs and link capacities as edge weights.
- **Solving** — finds all simple paths via BFS, assigns drones to paths using a capacity-aware greedy algorithm, then builds a turn-by-turn schedule that respects every occupancy, capacity and zone-type constraint.
- **Visualiser** — renders the map, animates drone movements along connection lines, and exposes playback controls through an interactive panel.

# Instructions
### Requirements
- Python 3.10 or later
- uv tool for dependency management

### Installation
Install dependencies using poetry:
```bash
make install
```

### Running the program
Runs the main program which parses, validates, solves and provides a visual simulation of the turns.
```bash
make run MAP=<path-to-map>
# or directly
uv run python3 main.py <path-to-map>
```

### Check source file linting
Runs checks of source file static typing using mypy, and norm using flake8.
```bash
make lint
```

### Debugging the program
Run the main script in debug mode using pdb.
```bash
make debug
```

### Cleaning up the project
Removes virtual environment .venv and temporary files or caches (e.g., pycache, .mypy__cache) to keep the project environment clean.
```bash
make clean
```

# Resources
- [Graph data structure](https://www.geeksforgeeks.org/dsa/graph-data-structure/)
- [Flow Network](https://brilliant.org/wiki/flow-network/)
- [Breadth first search](https://en.wikipedia.org/wiki/Breadth-first_search)
- [Maximum flow problems](https://en.wikipedia.org/wiki/Maximum_flow_problem)
- [Raylib](https://www.raylib.com/)


### AI Usage
AI was used as a development assistant throughout the project. The following tasks involved AI-generated or AI-assisted content, all of which was reviewed, understood and adapted before integration:
- **Separation of concerns**: Discussed the best way to split the project's layers: Parsing, Graph, Solver and Visualization layers.
- **Solver architecture**: Discussed the BFS algorithm for multi-path finding, and the two-phase turn scheduler design (leaving/arriving flow counters, restricted-zone wait mechanic). All logic and edge cases were manually reviewed before implementation.
- **Parser improvements**: Parsing enhancements and edge case handling suggestions like adding duplicate metadata key detection, and improving coordinate validation.
- **Documentation & Docstrings**: AI was used to draft docstring templates (Google style) which were then revised to accurately reflect the actual implementation.

AI was not used to generate code that was copy-pasted without understanding. In every case the generated output was read, questioned and modified to fit the project's specific requirements.

# Algorithm Explanation
My implementation of the algorithm runs through a pipeline of 4 steps:

### I. Graph Construction
The parsed map is converted into a directed weighted graph before any
pathfinding begins. Each zone becomes a `Node`; each bidirectional
connection becomes two directed `Edge` objects — one per direction.

Edge cost is determined by the **destination** zone type:

| Zone type | Move cost |
|---|---|
| `normal` | 1.0 |
| `priority` | 0.9 |
| `restricted` | 2.0 |
| `blocked` | ∞ (never entered) |

Edge capacity is set to the connection's `max_link_capacity` value
(default 1). Zone capacity (`max_drones`) is stored on the zone model
and enforced at scheduling time.

### II. Path discovery - BFS, top 2 paths retained
All simple paths from `start_hub` to `end_hub` are enumerated using
**breadth-first search**. Each BFS state carries the full path
accumulated so far rather than just the current node, which guarantees
simplicity — no zone is visited twice within a single path. Blocked
zones are pruned from the frontier immediately.

Every complete path is scored:

```
path_cost = len(path)
          + 1.0 × (number of restricted zones in path)
          − 0.1 × (number of priority zones in path)
```

Paths are computed once and cached inside the solver's instance; the scheduler never re-runs pathfinding.

Longer paths cost more; restricted zones are penalised because they
impose a mandatory wait turn before arrival; priority zones receive a
small bonus to make them preferred over equivalent normal routes.

Only the **two lowest-cost paths** are retained after sorting. Keeping
more paths does not improve performance on the provided maps because
additional paths are either longer, capacity-limited, or share the same
bottleneck zones as the top two.

---
### III. Drone assignment — greedy with cost bump

Drones are assigned to paths one at a time. At each step the drone is
placed on the path with the lowest current cost, then that path's cost
is bumped by `+1.0` before re-sorting:

```
for drone 1..N:
    assign drone to cheapest path
    raise cheapest path's cost by a bump of 1.0
    re-sort paths by cost
```

The `+1.0` bump acts as a soft capacity signal: once a path has
accumulated enough drones its cost overtakes the alternative, naturally
spreading the fleet across both routes.

---
### IV. Scheduling — turn-by-turn simulation

The scheduler builds a turn-by-turn simulation using the graph's objects to manage the flow.

#### State management:
- Drone tracking: Maintains `steps` (current drone's position in the assigned path), `waits` (cooldown for restricted zones), and a `delivered` set that tracks the delivered drones.
- Turn Reset: Every turn begins with `graph.reset()`, clearing the leaving, arriving and used counters on all nodes and edges.
- Turn Commit: After all possible moves are processed, `graph.commit_turn()` updates the permanent `drones_count` for each node based on that turn's flow.

#### Movement Constraints:
For each drone, a move is only valid if:
1. **Not waiting**: The drone is currently waiting on a connection towards a restricted zone.
2. **Link available**: The used edge hasn't reached its max capacity.
3. **Zone capacity**: The destination node has space, calculated as:
    $$
    max\_drones - (current + arriving - leaving) > 0
    $$

#### Restricted zones:
Upon enterin a restricted zone, `waits` is set to 1 for the arriving drone. This forces it to skip its next movement phase, making the transition cost 2 turns.

**Note**: By substracting `leaving` drones from the net drone count, the scheduler allows a drone to enter a full zone in the same turn another one leaves it.

# Visualization Specifications
## Visual Representation

The visualiser is built with **Raylib** via `pyray`(raylib's python bindings) and is split into two decoupled layers: a `MapLayout` that computes all pixel geometry once at startup, and a `MapRenderer` that consumes that geometry to draw and animate each frame.

---

### Layout layer (`layout.py`)

All coordinates, sizes and slot positions are derived from the parsed map at construction time. The renderer never does geometry arithmetic per frame.

**Zone sizing** is proportional to `max_drones`: a zone that holds more drones gets a larger circle. The slot grid inside each circle is a square of `⌈√max_drones⌉` cells, and the circle radius is the diagonal of that grid plus padding — so the circle always fits its contents.

**Grid alignment** ensures zones never overlap: the widest zone in each map column and the tallest zone in each map row set a uniform cell size for that column/row. Zones are then placed at cumulative column/row offsets, preserving the relative spatial layout from the map file.

**Connection lines** are clipped to the circle edges rather than drawn centre-to-centre. The connection endpoints are computed by normalising the direction vector between two zone centres and stepping inward by each zone's radius:

```
start = centre₁ + normalised_direction × radius₁
end   = centre₂ − normalised_direction × radius₂
```

This keeps the lines visually clean regardless of zone size differences.

**The control panel** is a fixed-height strip appended below the map area. Its turn-info label and three button rectangles are computed once and reused every frame as hit-test targets.

---

### Renderer layer (`renderer.py`)

**Zone colours** come directly from the `color=` metadata in the map file. Each zone is drawn with its parsed colour so zone types are immediately distinguishable at a glance. Zones with no valid colour get a rainbow gradient cycle as a fallback, making them visually distinct without crashing.

**Drone animation** uses a three-phase arc for each move:

| Phase | Motion |
|---|---|
| 0 | Current slot → connection start point (leaving the zone circle) |
| 1 | Connection start → connection end (traversing the link) |
| 2 | Connection end → target slot (entering the destination zone) |

Movement speed is a constant 300 px/s scaled by `get_frame_time()`, making the animation frame-rate independent. Each drone displays its numeric ID over the sprite so individual drones can be tracked through the animation.

The next turn is dispatched only when **all drones are idle** (`is_moving == False` for every drone), keeping the visual state fully consistent with the simulation state at all times.

**The control panel** provides three buttons built with Raylib's `gui_button`:

| Button | Behaviour |
|---|---|
| Play / Pause | Toggles continuous automatic playback |
| Next | Pauses and advances exactly one turn |
| Restart | Resets all drones to the start zone and replays from turn 0 |