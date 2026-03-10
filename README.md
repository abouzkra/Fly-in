*This project has been created as part of the 42 curriculum by abouzkra*

# Description
**Fly-in** is a drone fleet routing simulation written in Python. The goal is to move all drones from a central start hub to a target end hub across a network of connected zones, in the fewest possible simulation turns.
The program reads a custom map file that defines zones, connections, capacities and zone types, then computes an optimal routing plan and visualises the simulation in real time using **Raylib**.
The project is split into four independent layers:

- **Parser** — reads the map file format and builds an in-memory model, enforcing all syntactic and semantic constraints.
- **Graph** — constructs a directed weighted graph from the parsed map, encoding zone types as movement costs and link capacities as edge weights.
- **Solver** — finds all simple paths via BFS, assigns drones to paths using a capacity-aware greedy algorithm, then builds a turn-by-turn schedule that respects every occupancy, capacity and zone-type constraint.
- **Visualiser** — renders the map, animates drone movements along connection lines, and exposes playback controls through an interactive panel.

# Instructions
### Requirements
- Python 3.10 or later
- pip package manager

### Installation
Create and activate a virtual environment and install dependencies:
```bash
make install
source .venv/bin/activate
```

### Running the program
Runs the main program which parses, validates, solves and provides a visual simulation of the turns.
```bash
make run MAP=<path-to-map>
# or directly
poetry run python3 main.py <path-to-map>
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

# Additional sections
