MAIN = a_maze_ing.py
CONFIG = config.txt
CACHE = */__pycache__ .mypy_cache *.egg-info

all: run

build:
	python3 -m pip install build
	python3 -m build

install:
	python3 -m pip install -e .
	python3 -m pip install mazegen-1.0.0-py3-none-any.whl
	

run:
	python3 $(MAIN) $(CONFIG)

debug:
	python3 -m pdb $(MAIN) $(CONFIG)

clean:
	rm -rf build/ dist/
	rm -rf $(CACHE)
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

lint:
	flake8 .
	mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	flake8 .
	mypy . --strict


.PHONY: all build install clean run debug lint lint-strict