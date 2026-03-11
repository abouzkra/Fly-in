MAP = maps/easy/02_simple_fork.txt

MYPY_FLAGS = --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

install:
	@echo "Installing dependencies..."
	poetry install
	@echo "Dependencies installed successfully."

run:
	poetry run python3 main.py $(MAP)

debug:
	poetry run python3 -m pdb main.py $(MAP)

clean:
	rm -rf $$(find . -name "__pycache__" -o -name ".mypy_cache")
	@echo "Program cleaned successfully."

lint:
	poetry run flake8 . & poetry run mypy . $(MYPY_FLAGS) 
