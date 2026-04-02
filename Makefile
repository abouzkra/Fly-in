MAP = maps/hard/01_maze_nightmare.txt

MYPY_FLAGS = --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

install:
	@echo "Installing dependencies..."
	uv sync
	@echo "Dependencies installed successfully."

run:
	uv run python3 main.py $(MAP)

debug:
	uv run python3 -m pdb main.py $(MAP)

clean:
	rm -rf $$(find . -name "__pycache__" -o -name ".mypy_cache")
	rm uv.lock
	@echo "Program cleaned successfully."

lint:
	uv run flake8 . & uv run mypy . $(MYPY_FLAGS) 
