VENV = .venv

PYTHON = python3
PIP = ./$(VENV)/bin/pip
MYPY = ./$(VENV)/bin/mypy
FLAKE8 = ./$(VENV)/bin/flake8

PROGRAM_NAME = fly_in

PACKAGES_TO_INSTALL = mypy flake8 pydantic

PDB_COMMAND = $(PYTHON) -m pdb $(PROGRAM_NAME).py

CLEAN_COMMAND = rm -rf $$(find . -name "__pycache__" -o -name ".mypy_cache")

MYPY_FLAGS = --warn-return-any --warn-unused-ignores --ignore-missing-imports \
			--disallow-untyped-defs --check-untyped-defs

LINT_COMMAND = $(FLAKE8) . --exclude $(VENV) & $(MYPY) . $(MYPY_FLAGS) --exclude $(VENV)

CREATE_VENV = virtualenv $(VENV)

INSTALL_DEPS = $(PIP) install $(PACKAGES_TO_INSTALL)

install:
	@echo "Installing dependencies..."
	@$(CREATE_VENV)
	@$(INSTALL_DEPS)
	@echo "Dependencies installed successfully."

run:
	@$(PYTHON) $(PROGRAM_NAME).py

debug:
	@$(PDB_COMMAND)

clean:
	@$(CLEAN_COMMAND)
	@echo "Program cleaned successfully."

lint:
	$(LINT_COMMAND)
