import sys

try:
    from parsing import Parser
    from mazegen import MazeGenerator
except ImportError as e:
    print(f"Error: Missing required module -> {e}")
    sys.exit(1)


def main() -> None:
    """Parse arguments, validate config, and launch the interactive tool."""
    if len(sys.argv) != 2:
        print("Usage: python3 a_maze_ing.py <config_file>")
        sys.exit(1)

    config_file = sys.argv[1]

    try:
        config = Parser.validate_config(config_file)
        if config["algo"]:
            algo = config["algo"]
        else:
            algo = "dfs"

        seed = config["seed"]
        maze = MazeGenerator(
            config["width"],
            config["height"],
            config["entry"],
            config["exit"],
            config["perfect"],
            seed,
            algo,
        )
        maze.run_interactive(config["output_file"])
    except KeyboardInterrupt:
        print("\nExiting A-Maze-ing. Goodbye!")
        sys.exit(0)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
