.PHONY: help install install-dev test test-v test-cov test-failed test-watch test-unit test-integration test-cli test-new test-all test-ci test-act test-act-ubuntu test-act-windows test-act-macos clean lint format check docs build release

help:
	@echo "Development Commands:"
	@echo "  make install       - Install package in development mode"
	@echo "  make install-dev   - Install with development dependencies"
	@echo ""
	@echo "Testing Commands:"
	@echo "  make test          - Run all tests (excludes TDD)"
	@echo "  make test-v        - Run tests with verbose output"
	@echo "  make test-cov      - Run tests with coverage report"
	@echo "  make test-unit     - Run unit tests (core + vault)"
	@echo "  make test-integration - Run integration tests"
	@echo "  make test-cli      - Run CLI tests"
	@echo "  make test-new      - Run tests for new features"
	@echo "  make test-all      - Run ALL checks (format, lint, type, tests)"
	@echo "  make test-ci       - Run full CI/CD checks locally"
	@echo ""
	@echo "Act Testing (GitHub Actions locally):"
	@echo "  make test-act      - Run tests in GitHub Actions environment"
	@echo "  make test-act-ubuntu  - Test Ubuntu with Python 3.11"
	@echo "  make test-act-windows - Test Windows with Python 3.11"
	@echo "  make test-act-macos   - Test macOS with Python 3.11"
	@echo "  make test-act-py38    - Test Python 3.8 on Ubuntu"
	@echo "  make test-act-py39    - Test Python 3.9 on Ubuntu"
	@echo "  make test-act-all-ubuntu   - Test all Python versions on Ubuntu"
	@echo "  make test-act-all-os-py38  - Test Python 3.8 on all platforms"
	@echo "  make test-act-all-os-py39  - Test Python 3.9 on all platforms"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint          - Run code linting (flake8 + mypy)"
	@echo "  make format        - Format code with black and isort"
	@echo "  make check         - Check formatting without changing files"
	@echo ""
	@echo "Other Commands:"
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
	pytest -m "not tdd"

test-v:
	pytest -v -m "not tdd"

test-cov:
	pytest -m "not tdd" --cov=dayflow --cov-report=html --cov-report=term

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

# Run formatting check without modifying files
check:
	@echo "Checking code formatting..."
	black --check dayflow tests
	isort --check-only dayflow tests --profile black

# Run all CI/CD checks locally (matches GitHub Actions)
test-all: check lint test-cov
	@echo "All checks passed!"

# Run full CI/CD pipeline locally (exactly as GitHub Actions)
test-ci:
	@echo "Running full CI/CD checks (as in GitHub Actions)..."
	@echo "1. Checking formatting with black..."
	black --check dayflow tests
	@echo "2. Checking import sorting with isort..."
	isort --check-only dayflow tests --profile black
	@echo "3. Running flake8 linting..."
	flake8 dayflow tests --max-line-length=88 --extend-ignore=E203,W503
	@echo "4. Running mypy type checking..."
	mypy dayflow --ignore-missing-imports
	@echo "5. Running pytest with coverage..."
	pytest -m "not tdd" --cov=dayflow --cov-report=xml --cov-report=term
	@echo "✅ All CI/CD checks passed!"

# Act testing targets - single Python version
test-act:
	@echo "Running tests in GitHub Actions environment (Ubuntu, Python 3.11)..."
	act -j test --matrix os:ubuntu-latest --matrix python-version:3.11

test-act-ubuntu:
	@echo "Testing Ubuntu with Python 3.11..."
	act -j test --matrix os:ubuntu-latest --matrix python-version:3.11

test-act-windows:
	@echo "Testing Windows with Python 3.11..."
	act -j test --matrix os:windows-latest --matrix python-version:3.11

test-act-macos:
	@echo "Testing macOS with Python 3.11..."
	act -j test --matrix os:macos-latest --matrix python-version:3.11

# Act testing targets - specific Python versions
test-act-py38:
	@echo "Testing Python 3.8 on Ubuntu..."
	act -j test --matrix os:ubuntu-latest --matrix python-version:3.8

test-act-py39:
	@echo "Testing Python 3.9 on Ubuntu..."
	act -j test --matrix os:ubuntu-latest --matrix python-version:3.9

test-act-py310:
	@echo "Testing Python 3.10 on Ubuntu..."
	act -j test --matrix os:ubuntu-latest --matrix python-version:3.10

test-act-py311:
	@echo "Testing Python 3.11 on Ubuntu..."
	act -j test --matrix os:ubuntu-latest --matrix python-version:3.11

test-act-py312:
	@echo "Testing Python 3.12 on Ubuntu..."
	act -j test --matrix os:ubuntu-latest --matrix python-version:3.12

# Run act tests for all Python versions on a specific OS
test-act-all-ubuntu:
	@echo "Testing Ubuntu with all Python versions..."
	@for version in 3.8 3.9 3.10 3.11 3.12; do \
		echo "Testing Python $$version..."; \
		act -j test --matrix os:ubuntu-latest --matrix python-version:$$version; \
	done

test-act-all-windows:
	@echo "Testing Windows with all Python versions..."
	@for version in 3.8 3.9 3.10 3.11 3.12; do \
		echo "Testing Python $$version..."; \
		act -j test --matrix os:windows-latest --matrix python-version:$$version; \
	done

test-act-all-macos:
	@echo "Testing macOS with all Python versions..."
	@for version in 3.8 3.9 3.10 3.11 3.12; do \
		echo "Testing Python $$version..."; \
		act -j test --matrix os:macos-latest --matrix python-version:$$version; \
	done

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

# Test specific Python version on all OSes
test-act-all-os-py38:
	@echo "Testing Python 3.8 on all platforms..."
	@for os in ubuntu-latest windows-latest macos-latest; do \
		echo "Testing on $$os..."; \
		act -j test --matrix os:$$os --matrix python-version:3.8; \
	done

test-act-all-os-py39:
	@echo "Testing Python 3.9 on all platforms..."
	@for os in ubuntu-latest windows-latest macos-latest; do \
		echo "Testing on $$os..."; \
		act -j test --matrix os:$$os --matrix python-version:3.9; \
	done
