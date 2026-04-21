import sys
from typing import Any, Dict, Tuple


REQUIRED_KEYS = ["width", "height", "entry", "exit", "output_file", "perfect"]
OPTIONAL_KEYS = ["seed", "algo"]
ALL_KNOWN_KEYS = REQUIRED_KEYS + OPTIONAL_KEYS


def _read_file(filename: str) -> Dict[str, Any]:
    """
    Opens the config file and does the initial
      heavy lifting of cleaning up the text.

    It ignores comments and empty lines,
      checks that every setting actually has an
    equal sign, and makes sure we aren't
      missing any required settings or dealing
    with weird, unknown keys. If something looks wrong, it'll shut things down
    with a clear error message so the user knows exactly what to fix.
    """
    config: Dict[str, Any] = {}

    try:
        with open(filename, "r") as f:
            lines = f.read().splitlines()
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        sys.exit(1)

    except PermissionError:
        print(f"Error: File '{filename}' Not permitted.")
        sys.exit(1)

    try:
        for line in lines:
            if not line.strip() or line.startswith("#"):
                continue
            if "=" not in line:
                raise ValueError(f"Invalid line in config: '{line}'")

            key, value = line.split("=", 1)
            if key.strip().lower() in config:
                raise ValueError(f"{key.strip().lower()} is already found")
            config[key.strip().lower()] = value.strip()

        for key in REQUIRED_KEYS:
            if key not in config:
                raise ValueError(f"Missing required key: '{key}'")

        for key in config:
            if key not in ALL_KNOWN_KEYS:
                raise ValueError(f"Unknown key: '{key}'")

    except ValueError as e:
        print(f"Error parsing '{filename}': {e}")
        sys.exit(1)

    return config


def _parse_coord(raw: str, label: str) -> Tuple[int, int]:
    """
    Takes a string like '5,10'
    and turns it into a Python-friendly (row, col) tuple.

    The config file uses 'x,y' format,
      but since we usually work with (row, column)
    in code, this flips them to make the rest of the logic easier to follow.
    """
    parts = raw.split(",")
    if len(parts) != 2:
        raise ValueError(f"{label} must be in 'x,y' format")
    x, y = int(parts[0]), int(parts[1])
    return (y, x)


def _convert_types(config: Dict[str, Any]) -> None:
    """
    Changes the raw text from the config
      file into actual numbers, booleans, and tuples.

    This is where we get picky: we check if the maze is 'perfect', ensure the
    output filename makes sense (and won't overwrite the config!), and set up
    defaults for the random seed and the generation algorithm.
    """
    try:
        config["width"] = int(config["width"])
        config["height"] = int(config["height"])

        config["entry"] = _parse_coord(config["entry"], "ENTRY")
        config["exit"] = _parse_coord(config["exit"], "EXIT")

        if config["perfect"].lower() not in ("true", "false"):
            raise ValueError("PERFECT must be 'True' or 'False'")
        config["perfect"] = config["perfect"].lower() == "true"

        out = config["output_file"]
        if not out:
            raise ValueError("OUTPUT_FILE cannot be empty")
        if not out.endswith(".txt"):
            raise ValueError("OUTPUT_FILE must end with '.txt'")
        if out == "config.txt":
            raise ValueError("Overwriting 'config.txt' is forbidden")

        raw_seed = config.get("seed", None)
        if raw_seed == "" or raw_seed is None:
            config["seed"] = None
        else:
            config["seed"] = int(raw_seed)

        raw_algo = config.get("algo", "")
        algo = raw_algo.lower() if raw_algo else ""
        if algo and algo not in ("dfs", "prim"):
            raise ValueError("ALGO must be 'dfs' or 'prim'")
        config["algo"] = algo

    except ValueError as e:
        print(f"Error in configuration values: {e}")
        sys.exit(1)


def _check_ranges(config: Dict[str, Any]) -> None:
    """
    Sanity-checks the maze dimensions and
    coordinates to make sure they're realistic.

    We make sure the maze isn't too tiny (at least 3x3) or too massive for our
    system to handle. It also double-checks that the entry and exit points
    actually land inside the maze and aren't sitting on top of each other.
    """
    width: int = config["width"]
    height: int = config["height"]
    entry: Tuple[int, int] = config["entry"]
    exit_: Tuple[int, int] = config["exit"]

    if width <= 0 or height <= 0:
        print("Error: WIDTH and HEIGHT must be positive integers.")
        sys.exit(1)

    if width < 3 or height < 3:
        print("Error: WIDTH and HEIGHT must be at least 3.")
        sys.exit(1)

    if width > 300 or height > 280:
        print("Error: WIDTH must be <= 300 and HEIGHT must be <= 280.")
        sys.exit(1)

    entry_row, entry_col = entry
    exit_row, exit_col = exit_

    is_entry_valid = (0 <= entry_row < height) and (0 <= entry_col < width)
    is_exit_valid = (0 <= exit_row < height) and (0 <= exit_col < width)

    if not is_entry_valid:
        print("Error: ENTRY coordinates are outside the maze bounds.")
        sys.exit(1)

    if not is_exit_valid:
        print("Error: EXIT coordinates are outside the maze bounds.")
        sys.exit(1)

    if entry == exit_:
        print("Error: ENTRY and EXIT cannot be the same cell.")
        sys.exit(1)


class Parser:
    """
    The main coordinator for getting the maze configuration ready to go.
    """

    @staticmethod
    def validate_config(filename: str) -> Dict[str, Any]:
        """
        Runs the full validation pipeline: reading,
        converting, and range-checking.

        If this finishes successfully, you’ll get back a clean dictionary ready
        for use in the maze generator. If anything is off, it handles the
        errors internally and exits.
        """
        config = _read_file(filename)
        _convert_types(config)
        _check_ranges(config)
        return config
