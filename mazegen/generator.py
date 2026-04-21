import os
import random
import sys
import time
from collections import deque
from typing import Any, Callable, ClassVar, Dict, List, Optional, Set, Tuple


# Files that must never be overwritten by save_to_file.
_PROTECTED_FILES: Set[str] = {
    "makefile",
    "a_maze_ing.py",
    "maze_generator.py",
    "parsing.py",
    "pyproject.toml",
    "setup.py",
    ".gitignore",
}

# Dimension constraints enforced by MazeGenerator itself so the class
# remains correct when used as a standalone pip-installed package.
_MIN_WIDTH: int = 3
_MIN_HEIGHT: int = 3
_MAX_WIDTH: int = 300
_MAX_HEIGHT: int = 280

# Minimum dimensions required to render the '42' pattern.
_PATTERN_MIN_WIDTH: int = 9
_PATTERN_MIN_HEIGHT: int = 7

# ANSI escape codes for terminal colouring.
COLORS: Dict[str, str] = {
    "white": "\033[47m",
    "yellow": "\033[43m",
    "light_green": "\033[102m",
    "light_blue": "\033[104m",
    "gray": "\033[100m",
    "light_magenta": "\033[105m",
    "light_red": "\033[101m",
    "light_yellow": "\033[103m",
    "blue": "\033[44m",
    "magenta": "\033[45m",
    "red": "\033[41m",
    "cyan": "\033[46m",
    "reset": "\033[0m",
    "bold_white": "\033[97m\033[1m",
}

WALL_COLORS: List[str] = ["white", "light_green", "light_blue", "yellow"]
PATTERN_COLORS: List[str] = [
    "gray",
    "light_magenta",
    "light_red",
    "light_yellow",
    "blue",
]


class MazeGenerator:
    """
    The heart of the project. This class handles
      everything from carving out the
    labyrinth using different algorithms
      to rendering the results in your terminal.

    It keeps track of the grid state, the '42' pattern cells, and the final
    solution path.
    """

    NORTH: int = 1
    EAST: int = 2
    SOUTH: int = 4
    WEST: int = 8

    DIRS: ClassVar[List[int]] = [NORTH, EAST, SOUTH, WEST]

    DELTA: ClassVar[Dict[int, Tuple[int, int]]] = {
        NORTH: (-1, 0),
        EAST: (0, 1),
        SOUTH: (1, 0),
        WEST: (0, -1),
    }
    OPPOSITE: ClassVar[Dict[int, int]] = {
        NORTH: SOUTH,
        EAST: WEST,
        SOUTH: NORTH,
        WEST: EAST,
    }
    DIR_CHAR: ClassVar[Dict[int, str]] = {
        NORTH: "N",
        EAST: "E",
        SOUTH: "S",
        WEST: "W",
    }

    # Visual template: 'X' = wall cell, '.' = passable.
    # Dimensions: 5 rows x 7 cols - requires width >= 9 and height >= 7.
    PATTERN_42: ClassVar[List[str]] = [
        "X...XXX",
        "X.....X",
        "XXX.XXX",
        "..X.X..",
        "..X.XXX",
    ]

    def __init__(
        self,
        width: int,
        height: int,
        entry: Tuple[int, int],
        exit_pos: Tuple[int, int],
        perfect: bool,
        seed: Optional[int],
        algo: str = "dfs",
    ) -> None:
        """
        Sets up the maze's internal state.

        It checks if the dimensions make sense,
          prepares the grid (where every cell
        starts as a solid block of four walls), and reserves the space for the
        '42' logo so the algorithms don't accidentally carve through it.
        """
        self._validate_dimensions(width, height)

        self.width = width
        self.height = height
        self.entry = entry
        self.exit_pos = exit_pos
        self.perfect = perfect
        self.seed: int = random.randint(1, 9999) if seed is None else seed
        self.algo: str = algo or "dfs"

        self.path: str = ""
        self.path_coords: List[Tuple[int, int]] = []
        self.pattern_cells: Set[Tuple[int, int]] = set()

        # All walls closed by default (15 = 0b1111).
        self.grid: List[List[int]] = [[15] * width for _ in range(height)]
        self._visited: List[List[bool]] = [[False] * width
                                           for _ in range(height)]

        # Validate entry and exit after grid is sized.
        self._validate_entry_exit(entry, exit_pos)

        # Draw '42' or warn if too small (subject: print, not crash).
        if width >= _PATTERN_MIN_WIDTH and height >= _PATTERN_MIN_HEIGHT:
            self._draw_42()
        else:
            print(
                f"Info: Maze size {width}x{height} is too small to render "
                f"the '42' pattern (requires >= {_PATTERN_MIN_WIDTH}x"
                f"{_PATTERN_MIN_HEIGHT})."
            )

        if entry in self.pattern_cells or exit_pos in self.pattern_cells:
            raise ValueError(
                "ENTRY or EXIT coordinate overlaps with the '42' pattern. "
                "Choose different coordinates."
            )

    @staticmethod
    def _validate_dimensions(width: int, height: int) -> None:
        """
        Makes sure we aren't trying to build
          a maze that's physically impossible
        or so huge it'll crash the terminal.
        """
        if width < _MIN_WIDTH or height < _MIN_HEIGHT:
            raise ValueError(
                f"Maze dimensions {width}x{height} are too small. "
                f"Minimum allowed is {_MIN_WIDTH}x{_MIN_HEIGHT}."
            )
        if width > _MAX_WIDTH or height > _MAX_HEIGHT:
            raise ValueError(
                f"Maze dimensions {width}x{height} exceed the maximum. "
                f"Maximum allowed is {_MAX_WIDTH}x{_MAX_HEIGHT}."
            )

    def _validate_entry_exit(
        self,
        entry: Tuple[int, int],
        exit_pos: Tuple[int, int],
    ) -> None:
        """
        Makes sure the entrance and exit are actually inside the maze and
        aren't sitting on the exact same spot. Raises a ValueError if things
        don't line up.
        """
        if not self._in_bounds(*entry):
            raise ValueError(
                f"ENTRY {entry} is outside the maze bounds "
                f"({self.height}x{self.width})."
            )
        if not self._in_bounds(*exit_pos):
            raise ValueError(
                f"EXIT {exit_pos} is outside the maze bounds "
                f"({self.height}x{self.width})."
            )
        if entry == exit_pos:
            raise ValueError("ENTRY and EXIT cannot be the same cell.")

    def _in_bounds(self, row: int, col: int) -> bool:
        """
        A quick safety check to confirm if a specific (row, col) coordinate
        actually exists within our grid's boundaries.
        """
        return 0 <= row < self.height and 0 <= col < self.width

    def _draw_42(self) -> None:
        """
        Stamps the '42' logo right in the middle of the maze.

        It reads our visual template and marks
          those specific cells as 'visited'
        before generation starts. This tells
          the algorithms to leave them alone,
        keeping the walls solid block.
        """
        origin_row = self.height // 2 - 2
        origin_col = self.width // 2 - 3

        for dr, row_str in enumerate(self.PATTERN_42):
            for dc, char in enumerate(row_str):
                if char != "X":
                    continue
                row, col = origin_row + dr, origin_col + dc
                if self._in_bounds(row, col):
                    self._visited[row][col] = True
                    self.pattern_cells.add((row, col))

    def _carve_wall(
        self,
        row1: int,
        col1: int,
        row2: int,
        col2: int,
        direction: int,
    ) -> None:
        """
        The hammer and chisel of the generator.

        We use bitwise math here to knock down a wall in the current cell and
        simultaneously smash the corresponding wall in the neighboring cell.
        """
        self.grid[row1][col1] &= ~direction
        self.grid[row2][col2] &= ~self.OPPOSITE[direction]

    def _dfs(
        self,
        start_row: int,
        start_col: int,
        callback: Optional[Callable[[], None]] = None,
    ) -> None:
        """
        The classic Depth-First Search approach.

        Imagine wandering through a house, picking random doors until you hit
        a dead end, then backtracking. We use an explicit stack here instead of
        recursion to keep Python from hitting its recursion
          limit on massive mazes.
        The callback hook lets us pause and draw the maze
          frame-by-frame if we want to animate it.
        """
        self._visited[start_row][start_col] = True
        stack: List[Tuple[int, int]] = [(start_row, start_col)]

        while stack:
            row, col = stack[-1]
            dirs = self.DIRS[:]
            random.shuffle(dirs)

            moved = False
            for direction in dirs:
                dr, dc = self.DELTA[direction]
                nr, nc = row + dr, col + dc
                if self._in_bounds(nr, nc) and not self._visited[nr][nc]:
                    self._visited[nr][nc] = True
                    self._carve_wall(row, col, nr, nc, direction)
                    stack.append((nr, nc))
                    if callback:
                        callback()
                    moved = True
                    break

            if not moved:
                stack.pop()

    def _prim(
        self,
        start_row: int,
        start_col: int,
        callback: Optional[Callable[[], None]] = None,
    ) -> None:
        """
        Randomized Prim's algorithm.

        Instead of diving deep like DFS, this grows outward like a crystal.
        It keeps a 'frontier' list of available walls and picks one at random
        to knock down. This tends to create mazes
          with a ton of short, winding dead ends.
        We use a swap-and-pop trick on the frontier
          list to keep it fast (O(1) deletion).
        """
        self._visited[start_row][start_col] = True
        frontier: List[Tuple[int, int, int]] = [
            (start_row, start_col, d) for d in self.DIRS
        ]

        while frontier:
            idx = random.randrange(len(frontier))
            frontier[idx], frontier[-1] = frontier[-1], frontier[idx]
            row, col, direction = frontier.pop()

            dr, dc = self.DELTA[direction]
            nr, nc = row + dr, col + dc

            if not self._in_bounds(nr, nc) or self._visited[nr][nc]:
                continue

            self._visited[nr][nc] = True
            self._carve_wall(row, col, nr, nc, direction)
            if callback:
                callback()

            for d in self.DIRS:
                frontier.append((nr, nc, d))

    def _add_loops(
        self,
        n_loops: int,
        callback: Optional[Callable[[], None]] = None,
    ) -> None:
        """
        Takes a 'perfect' maze (one with exactly one solution) and punches
        some extra holes in it to create loops.

        To keep it efficient, we pre-calculate all the safe internal walls that
        don't touch our '42' logo, shuffle that list, and then knock down the
        requested number of walls.
        """
        candidates: List[Tuple[int, int, int]] = []
        for row in range(1, self.height - 1):
            for col in range(1, self.width - 1):
                if (row, col) in self.pattern_cells:
                    continue
                for direction in self.DIRS:
                    dr, dc = self.DELTA[direction]
                    nr, nc = row + dr, col + dc
                    if (nr, nc) in self.pattern_cells:
                        continue
                    if not self._in_bounds(nr, nc):
                        continue
                    if self.grid[row][col] & direction:
                        candidates.append((row, col, direction))

        random.shuffle(candidates)
        removed = 0
        for row, col, direction in candidates:
            if removed >= n_loops:
                break

            if not (self.grid[row][col] & direction):
                continue

            dr, dc = self.DELTA[direction]
            nr, nc = row + dr, col + dc

            if (self.grid[row][col] & ~direction) == 0:
                continue
            if (self.grid[nr][nc] & ~self.OPPOSITE[direction]) == 0:
                continue

            self._carve_wall(row, col, nr, nc, direction)
            removed += 1
            if callback:
                callback()

    def _find_path(self) -> None:
        """
        Uses Breadth-First Search (BFS) to hunt
          down the absolute shortest route
        from the entry to the exit.

        Since BFS expands outward evenly level-by-level, the exact moment it
        steps on the exit tile, we know we've found the optimal path. It saves
        both the directional string (N, S, E, W) and the coordinates.
        """
        queue: deque[Tuple[Tuple[int, int], str,
                           List[Tuple[int, int]]]] = deque(
            [(self.entry, "", [self.entry])]
        )
        seen: Set[Tuple[int, int]] = {self.entry}

        while queue:
            (row, col), directions, coords = queue.popleft()

            if (row, col) == self.exit_pos:
                self.path = directions
                self.path_coords = coords
                return

            for direction, (dr, dc) in self.DELTA.items():
                nr, nc = row + dr, col + dc
                if (
                    self._in_bounds(nr, nc)
                    and not (self.grid[row][col] & direction)
                    and (nr, nc) not in seen
                ):
                    seen.add((nr, nc))
                    queue.append(
                        (
                            (nr, nc),
                            directions + self.DIR_CHAR[direction],
                            coords + [(nr, nc)],
                        )
                    )

    def generate(
        self,
        algo: str = "dfs",
        callback: Optional[Callable[[], None]] = None,
    ) -> None:
        """
        The main orchestrator.

        It locks in the random seed
        (so we can recreate specific mazes if needed),
        fires up the chosen carving algorithm,
          optionally blasts some extra loops
        into the walls if we asked for an imperfect maze,
          and finally solves it.
        """
        random.seed(self.seed)
        algo = algo.lower()

        if algo in ("dfs", ""):
            self._dfs(0, 0, callback)
        elif algo == "prim":
            self._prim(0, 0, callback)

        if not self.perfect:
            n_loops = max(1, (self.width * self.height) // 7)
            self._add_loops(n_loops, callback)

        self._find_path()

    def save_to_file(self, filename: str) -> None:
        """
        Dumps the generated maze and its solution into a text file, formatted
        exactly how the A-Maze-ing project subject demands.

        It also has safeguards built-in so you don't accidentally overwrite
        critical project files like the makefile or these python scripts.
        """
        # Block overwriting critical project files.
        basename = os.path.basename(filename).lower()
        if basename in _PROTECTED_FILES:
            raise ValueError(
                f"Writing to '{filename}' is forbidden - "
                "it is a protected project file."
            )

        # Block writing to a directory path.
        if os.path.isdir(filename):
            raise IsADirectoryError(f"'{filename}'"
                                    f"is a directory, not a file.")

        try:
            with open(filename, "w") as f:
                for row in self.grid:
                    f.write("".join(f"{cell:X}" for cell in row) + "\n")
                f.write("\n")
                f.write(f"{self.entry[1]},{self.entry[0]}\n")
                f.write(f"{self.exit_pos[1]},{self.exit_pos[0]}\n")
                f.write(f"{self.path}\n")
        except PermissionError:
            print(f"Error: No permission to write '{filename}'.")
        except OSError as e:
            print(f"Error writing '{filename}': {e}")

    def _clear_screen(self) -> None:
        """Wipes the terminal completely clean so we can draw a fresh frame."""
        sys.stdout.write("\033[H\033[J")
        sys.stdout.flush()

    def _reset_cursor(self) -> None:
        """
        Snaps the terminal cursor back to the top-left corner without clearing
        the whole screen. This is a neat trick to drastically
          reduce screen tearing
        and flicker when we're animating the maze generation.
        """
        sys.stdout.write("\033[H")
        sys.stdout.flush()

    def render_maze(
        self,
        show_path: bool,
        wall_color: str,
        pattern_color: str,
    ) -> None:
        """
        Paints the maze in the terminal using ANSI color codes.

        It translates our underlying bitwise
          grid into visual 2-character blocks,
        highlighting the walls, the path,
          the entrance/exit, and the '42' pattern
        using whatever colors are currently active.
        """
        rows = self.height * 2 + 1
        cols = self.width * 2 + 1
        display: List[List[str]] = [["  " for _ in range(cols)]
                                    for _ in range(rows)]

        wall_c = f"{COLORS[wall_color]}  {COLORS['reset']}"
        empty_c = "  "
        pattern_c = f"{COLORS[pattern_color]}  {COLORS['reset']}"
        path_c = f"{COLORS['cyan']}  {COLORS['reset']}"
        entry_c = (f"{COLORS['magenta']}"
                   f"{COLORS['bold_white']}IN{COLORS['reset']}")
        exit_c = f"{COLORS['red']}{COLORS['bold_white']}EX{COLORS['reset']}"

        # All even-row / even-col intersections are wall corners.
        for r in range(rows):
            for c in range(cols):
                if r % 2 == 0 and c % 2 == 0:
                    display[r][c] = wall_c

        # Fill cell centres and wall segments from the grid bit values.
        for r in range(self.height):
            for c in range(self.width):
                tr, tc = r * 2 + 1, c * 2 + 1
                val = self.grid[r][c]

                if (r, c) == self.entry:
                    display[tr][tc] = entry_c
                elif (r, c) == self.exit_pos:
                    display[tr][tc] = exit_c
                elif show_path and (r, c) in self.path_coords:
                    display[tr][tc] = path_c
                elif (r, c) in self.pattern_cells:
                    display[tr][tc] = pattern_c
                else:
                    display[tr][tc] = empty_c

                # North=1, East=2, South=4, West=8
                if val & 1:
                    display[tr - 1][tc] = wall_c
                if val & 4:
                    display[tr + 1][tc] = wall_c
                if val & 2:
                    display[tr][tc + 1] = wall_c
                if val & 8:
                    display[tr][tc - 1] = wall_c

        # Connect adjacent path cells through open walls.
        if show_path:
            for i in range(len(self.path_coords) - 1):
                r1, c1 = self.path_coords[i]
                r2, c2 = self.path_coords[i + 1]
                display[r1 + r2 + 1][c1 + c2 + 1] = path_c

        sys.stdout.write("\n".join("".join(row) for row in display) + "\n")
        sys.stdout.flush()

    def _create_maze(
        self,
        output_file: str,
        use_seed: bool,
        algo: str,
        animate: bool,
        wall_color: str,
        pattern_color: str,
    ) -> "MazeGenerator":
        """
        A handy factory method. It spins up a new MazeGenerator instance,
        optionally runs the generation with a step-by-step animation, saves the
        result to a file, and hands the completed maze object back to you.
        """
        seed = self.seed if use_seed else None

        maze = MazeGenerator(
            width=self.width,
            height=self.height,
            entry=self.entry,
            exit_pos=self.exit_pos,
            perfect=self.perfect,
            seed=seed,
            algo=algo,
        )

        if animate:
            maze._clear_screen()
            total_cells = maze.width * maze.height
            if total_cells < 150:
                delay = 0.05
            elif total_cells < 400:
                delay = 0.01
            else:
                delay = 0.001

            def anim_callback() -> None:
                maze._reset_cursor()
                if maze.height < 7 or maze.width < 9:
                    print(
                        f"{COLORS['red']}Warning the maze is too small "
                        f"to fit 42!{COLORS['reset']}"
                    )
                maze.render_maze(False, wall_color, pattern_color)
                time.sleep(delay)

            maze.generate(algo=algo, callback=anim_callback)
        else:
            maze.generate(algo=algo)

        maze.save_to_file(output_file)
        return maze

    def run_interactive(self, output_file: str) -> None:
        """
        The main terminal GUI loop.

        This drops the user into an interactive menu where they can endlessly
        generate new mazes, watch the algorithms animate, toggle the shortest
        solution path, and mess around with the terminal color schemes.
        """
        state: Dict[str, Any] = {
            "algo": self.algo or "dfs",
            "show_path": False,
            "w_idx": 0,
            "p_idx": 0,
            "warning": "",
        }

        def make_maze(
            use_seed: bool,
            animate: bool = False,
        ) -> "MazeGenerator":
            return self._create_maze(
                output_file,
                use_seed,
                algo=state["algo"],
                animate=animate,
                wall_color=WALL_COLORS[state["w_idx"]],
                pattern_color=PATTERN_COLORS[state["p_idx"]],
            )

        maze = make_maze(use_seed=True)

        while True:
            self._clear_screen()
            if maze.height < 7 or maze.width < 9:
                print(
                    f"{COLORS['red']}Warning: the maze is too small to "
                    f"fit 42!{COLORS['reset']}"
                )

            maze.render_maze(
                state["show_path"],
                WALL_COLORS[state["w_idx"]],
                PATTERN_COLORS[state["p_idx"]],
            )

            print("\n====== A-Maze-ing ======\n")
            print("1. Re-generate a new maze")
            print("2. Animate a new maze")
            print("3. Toggle algorithm     "
                  f"[current: {state['algo'].upper()}]")
            vis = "Visible" if state["show_path"] else "Hidden"
            print(f"4. Show/Hide path       [current: {vis}]")
            print(
                f"5. Rotate wall colour   "
                f"[current: "
                f"{WALL_COLORS[state['w_idx']]}]"
            )
            print(
                f"6. Rotate '42' colour   "
                f"[current: "
                f"{PATTERN_COLORS[state['p_idx']]}]"
            )
            print("7. Quit")

            if state["warning"]:
                print(f"\033[91m[!] {state['warning']}\033[0m")
                state["warning"] = ""

            try:
                choice = input("\nChoice? (1-7): ").strip()
            except EOFError:
                break

            if choice == "1":
                maze = make_maze(use_seed=False)
            elif choice == "2":
                maze = make_maze(use_seed=False, animate=True)
            elif choice == "3":
                state["algo"] = "prim" if state["algo"] == "dfs" else "dfs"
                maze = make_maze(use_seed=False)
                state["warning"] = (f"Algorithm switched "
                                    f"to {state['algo'].upper()}.")
            elif choice == "4":
                state["show_path"] = not state["show_path"]
            elif choice == "5":
                state["w_idx"] = (state["w_idx"] + 1) % len(WALL_COLORS)
            elif choice == "6":
                state["p_idx"] = (state["p_idx"] + 1) % len(PATTERN_COLORS)
            elif choice == "7":
                break
            else:
                state["warning"] = (
                    "Invalid choice. Please enter a " "number between 1 and 7."
                )
