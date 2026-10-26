# Makefile for gridqueue-grid-connection
# Requires uv (https://docs.astral.sh/uv/): curl -LsSf https://astral.sh/uv/install.sh | sh

UV ?= uv
BACKEND := backend

.PHONY: help sample check test lint format typecheck api clean require-uv

help:
	@echo "Available commands:"
	@echo "  make sample    - Offline, no API key: gate + contracts + /v1/answer on SYNTHETIC fixtures"
	@echo "  make check     - Lint, typecheck and run the full test suite (what CI runs)"
	@echo "  make test      - Run the full pytest suite"
	@echo "  make lint      - ruff lint + format check"
	@echo "  make format    - Apply ruff formatting and safe fixes"
	@echo "  make typecheck - mypy over backend/app"
	@echo "  make api       - Start the FastAPI server on 0.0.0.0:8000"
	@echo "  make clean     - Remove virtualenvs, caches and build artifacts"

require-uv:
	@command -v $(UV) >/dev/null 2>&1 || { echo "uv not found. Install: curl -LsSf https://astral.sh/uv/install.sh | sh"; exit 1; }

# Offline, no key: the gate, the contracts, and POST /v1/answer replayed end to end on the SYNTHETIC fixtures
# in data/fixtures/synthetic/ (live-path tests in that file use mocked Tavily/model clients, no network).
sample: require-uv
	cd $(BACKEND) && $(UV) run --extra dev pytest tests/test_gate.py tests/test_schemas.py tests/test_answer_api.py -v

check: lint typecheck test

test: require-uv
	cd $(BACKEND) && $(UV) run --extra dev pytest -v

lint: require-uv
	cd $(BACKEND) && $(UV) run --extra dev ruff check . && $(UV) run --extra dev ruff format --check .

format: require-uv
	cd $(BACKEND) && $(UV) run --extra dev ruff check --fix . && $(UV) run --extra dev ruff format .

typecheck: require-uv
	cd $(BACKEND) && $(UV) run --extra dev mypy

api: require-uv
	cd $(BACKEND) && $(UV) run gridqueue-api

clean:
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -prune -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -prune -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -prune -exec rm -rf {} +
	rm -rf $(BACKEND)/.venv frontend/node_modules
