MAP = maps/medium/03_priority_puzzle.txt

MYPY_FLAGS = --exclude .venv --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

install:
	@echo "Installing dependencies..."
	uv sync
	@echo "Dependencies installed successfully."

run:
	uv run python3 main.py $(MAP)

debug:
	uv run python3 -m pdb main.py $(MAP)

clean:
	rm -rf .venv/
	rm -rf $$(find . -name "__pycache__" -o -name ".mypy_cache")
	rm uv.lock
	@echo "Program cleaned successfully."

lint:
	uv run flake8 --exclude .venv . & uv run mypy . $(MYPY_FLAGS) 
