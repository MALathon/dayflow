.PHONY: help install install-dev test test-v test-cov test-failed test-watch test-unit test-integration test-cli test-new clean lint format docs build release

help:
	@echo "Development Commands:"
	@echo "  make install       - Install package in development mode"
	@echo "  make install-dev   - Install with development dependencies"
	@echo "  make test          - Run all tests"
	@echo "  make test-v        - Run tests with verbose output"
	@echo "  make test-cov      - Run tests with coverage report"
	@echo "  make test-unit     - Run unit tests (core + vault)"
	@echo "  make test-integration - Run integration tests"
	@echo "  make test-cli      - Run CLI tests"
	@echo "  make test-new      - Run tests for new features"
	@echo "  make lint          - Run code linting (flake8)"
	@echo "  make format        - Format code with black and isort"
	@echo "  make clean         - Remove cache and build files"
	@echo "  make docs          - Build documentation"
	@echo "  make build         - Build distribution packages"
	@echo "  make release       - Upload to PyPI (configure credentials first)"

install:
	pip install -e .

install-dev:
	pip install -e .
	pip install -r requirements-dev.txt
	pre-commit install

test:
	pytest

test-v:
	pytest -v

test-cov:
	pytest --cov=dayflow --cov-report=html --cov-report=term

test-failed:
	pytest --lf

test-watch:
	ptw

test-unit:
	pytest tests/core tests/vault -v

test-integration:
	pytest tests/integration -v

test-cli:
	pytest tests/ui/cli -v

test-new:
	pytest tests/core/test_daily_summary.py tests/core/test_meeting_matcher.py tests/ui/cli/test_note_command.py tests/ui/cli/test_status_command.py -v

lint:
	flake8 dayflow tests --max-line-length=88 --extend-ignore=E203,W503
	mypy dayflow --ignore-missing-imports

format:
	black dayflow tests
	isort dayflow tests --profile black

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name htmlcov -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".coverage" -delete
	rm -rf build/ dist/

docs:
	@echo "Documentation building not configured yet."
	@echo "Run: pip install -e .[docs] then sphinx-quickstart in docs/"

build: clean
	python -m build

release: build
	@echo "To upload to PyPI:"
	@echo "  python -m twine upload dist/*"
	@echo "Make sure you have configured ~/.pypirc with your credentials"