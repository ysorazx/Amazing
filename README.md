*This project has been created as part of the 42 curriculum by <ilaghrai> <yramouch>.*

# A-Maze-ing

## Description
**A-Maze-ing** is a complete Python-based maze generator and solver. The project creates procedurally generated mazes based on configuration parameters, guaranteeing valid connectivity from an entry to an exit point. It can generate both "perfect" mazes (a single unique path between any two cells) and imperfect mazes (containing loops). 

The generated maze is embedded with a hidden, uncarved "42" pattern and is interactively rendered in the terminal using ANSI colors. Additionally, the maze data is exported to a file using hexadecimal bitmask encoding to represent the walls of each cell.

## Instructions

### Prerequisites
- **Python:** 3.10 or later
- **Make** (optional, but recommended for automated tasks)

### Execution
You can run the project directly from the terminal by providing a configuration file:
```bash
python3 a_maze_ing.py config.txt
```

Alternatively, use the provided `Makefile` commands to manage the project:
- `make install`: Install dependencies and/or the reusable package.
- `make run`: Run the program using the default `config.txt`.
- `make lint`: Run `flake8` and `mypy` for code quality checks.
- `make debug`: Run the program with the built-in python debugger.
- `make clean`: Clean up python cache files (`__pycache__`, etc.).

### Interactive Visualizer
Once launched, the terminal will render the maze and present an interactive menu allowing you to:
1. Re-generate a new maze randomly.
2. **Animate** the generation of a new maze step-by-step.
3. Toggle the generation algorithm (DFS vs Prim).
4. Show or hide the shortest path to the exit.
5. Cycle through different maze wall and "42" pattern colors.

## Configuration File Structure
The project relies on a plain text configuration file (e.g., `config.txt`). It uses a `KEY=VALUE` format. Lines starting with `#` are ignored.

**Mandatory Keys:**
- `WIDTH`: Width of the maze (integer, 3 to 300).
- `HEIGHT`: Height of the maze (integer, 3 to 280).
- `ENTRY`: Starting coordinates in `x,y` (column,row) format.
- `EXIT`: Exit coordinates in `x,y` format.
- `OUTPUT_FILE`: Destination file for the generated hexadecimal maze (must end in `.txt`).
- `PERFECT`: Boolean (`True` or `False`). If `False`, loops are added to the maze.

**Optional Keys:**
- `SEED`: Integer to seed the random number generator for reproducibility.
- `ALGO`: The algorithm to use for generation (`dfs` or `prim`).

*Example:*
```ini
WIDTH=20
HEIGHT=15
ENTRY=0,0
EXIT=19,14
OUTPUT_FILE=maze.txt
PERFECT=False
SEED=42
ALGO=dfs
```

## Maze Generation Algorithms

### Algorithms Chosen
1. **Iterative Depth-First Search (DFS) (Default):** Generates mazes with a low branching factor and long, winding corridors, making them visually challenging.
2. **Randomized Prim's Algorithm:** Generates mazes with a high branching factor and many short dead-ends, creating a very distinct, "uniform" visual texture.

### Why these algorithms?
I chose **DFS** because it is a classic maze-generation algorithm that creates high "river" characteristics (long, winding paths) which are highly satisfying for human solvers. It was implemented iteratively using a stack to prevent Python recursion depth limits. 
I added **Prim's algorithm** to provide a highly contrasting visual generation style and to fulfill the advanced bonus features.

## Reusable Module

The core logic of the maze generation is strictly isolated in the `mazegen.py` file inside the `MazeGenerator` class. This makes it a highly reusable, standalone module.

### Installation
As per the requirements, this module is bundled into a package that can be installed via `pip`. 
From the root of the repository, once built:
```bash
pip install mazegen-1.0.0-py3-none-any.whl
```

### Usage Example
```python
from mazegen import MazeGenerator

# 1. Instantiate the generator
maze = MazeGenerator(
    width=20, 
    height=15, 
    entry=(0, 0),     # (row, col)
    exit_pos=(14, 19), # (row, col)
    perfect=True, 
    seed=123
)

# 2. Generate the maze using the algorithm of choice
maze.generate(algo="dfs")

# 3. Access the generated structure
# maze.grid contains the 2D array of cells (hexadecimal bitmask format)
# maze.path_coords contains the list of (row, col) tuples forming the solution

# 4. Save to file
maze.save_to_file("my_maze.txt")
```

## Team and Project Management

* **Roles:** 
  *[Your Name] - Sole Developer (Architecture, Algorithms, Visualization, Documentation).
* **Anticipated Planning & Evolution:**
  1. *Phase 1:* Set up standard configuration parsing (`parsing.py`) and basic constraints.
  2. *Phase 2:* Implement the `MazeGenerator` logic with bitwise operations, starting with DFS.
  3. *Phase 3:* Implement BFS pathfinding and the "42" static pattern blocking.
  4. *Phase 4:* Implement terminal rendering and interactivity (`a_maze_ing.py`).
  *Evolution:* Originally planned to only do DFS, but the bitwise wall carving architecture made it remarkably easy to plug in Prim's algorithm as well, so the scope was slightly expanded to support multiple algorithms.
* **What worked well & What could be improved:**
  * *Worked well:* Using bitwise tracking for cell walls (1=N, 2=E, 4=S, 8=W) was extremely efficient and made generating the hexadecimal output trivial.
  * *Could be improved:* The terminal rendering uses 2x2 character blocks, which works beautifully but limits the maximum visual size on smaller screens. A graphical MLX version could be implemented later to scale infinitely.
* **Specific Tools Used:**
  * `flake8` and `mypy` for strict typing and static analysis.
  * `build` / `setuptools` to package the `.whl` and `.tar.gz` reusable module.

## Bonuses / Advanced Features
- **Multiple Algorithms:** Users can switch between DFS and Prim's algorithm on the fly.
- **Terminal Animations:** Step-by-step rendering animation during the maze carving process.
- **Interactive UI:** A full terminal menu that lets the user regenerate, re-seed, toggle solutions, and recolor the maze live without restarting the program.

## Resources
* **Maze Generation Algorithms:** [Wikipedia - Maze generation algorithm](https://en.wikipedia.org/wiki/Maze_generation_algorithm)
* **Hexadecimal Bitmasking:** Concept adapted from classic tile-mapping graph theories.
* **AI Usage:** AI was used in this project primarily as a learning assistant to clarify edge-cases in `mypy` typing, format the docstrings into a clean standard (Google style), and discover the correct ANSI escape codes required to prevent terminal flickering during the live animation step. 