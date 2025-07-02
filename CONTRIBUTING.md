# Contributing to Dayflow

Thank you for your interest in contributing to Dayflow!

## Getting Started

### Development Setup

1. Fork and clone the repository:
   ```bash
   git clone https://github.com/yourusername/dayflow.git
   cd dayflow
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install in development mode:
   ```bash
   pip install -e .
   pip install -r requirements-dev.txt
   ```

4. Set up pre-commit hooks:
   ```bash
   pre-commit install
   ```

5. (Optional) Install `act` for local GitHub Actions testing:
   ```bash
   # macOS
   brew install act

   # Linux
   curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

   # Windows (using Chocolatey)
   choco install act-cli
   ```

### Running Tests

```bash
# Quick test run
make test

# Run full CI/CD pipeline locally (matches GitHub Actions exactly)
make test-ci

# Run all checks (format, lint, type, tests)
make test-all

# Run specific test categories
make test-unit          # Unit tests only
make test-integration   # Integration tests
make test-cli          # CLI tests
make test-cov          # With coverage report

# Test with GitHub Actions locally using act
make test-act          # Default: Ubuntu + Python 3.11
make test-act-windows  # Windows + Python 3.11
make test-act-macos    # macOS + Python 3.11

# Test all Python versions on a specific OS
make test-act-all-ubuntu   # Tests Python 3.8-3.12 on Ubuntu
make test-act-all-windows  # Tests Python 3.8-3.12 on Windows
make test-act-all-macos    # Tests Python 3.8-3.12 on macOS

# Direct pytest commands
pytest tests/test_meeting_matcher.py   # Single file
pytest -m integration                  # Integration tests only
pytest -v --durations=10              # Verbose with timing
```

## Development Guidelines

### Code Style

We use:
- **Black** for code formatting
- **isort** for import sorting
- **Flake8** for linting
- **mypy** for type checking (optional but encouraged)

Run formatting:
```bash
black dayflow tests
isort dayflow tests
```

### Commit Messages

Follow conventional commit format:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Test additions or changes
- `refactor:` Code refactoring
- `chore:` Maintenance tasks

Examples:
```
feat: add support for recurring meetings
fix: handle timezone conversion errors
docs: update vault setup guide
test: add tests for daily summary generator
```

### Pull Request Process

1. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes following TDD:
   - Write failing tests first
   - Implement the feature
   - Ensure all tests pass

3. Update documentation:
   - Update relevant .md files
   - Add docstrings to new functions/classes
   - Update CHANGELOG.md

4. Submit PR:
   - Clear description of changes
   - Reference any related issues
   - Include test results

## Testing Guidelines

### Test Organization

```
tests/
├── core/              # Core functionality tests
├── vault/             # Vault management tests
├── ui/                # CLI interface tests
└── integration/       # End-to-end tests
```

### Test Markers

- `@pytest.mark.tdd` - Test-driven development tests (skipped by default)
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.slow` - Long-running tests
- `@pytest.mark.requires_token` - Tests requiring Microsoft Graph token

### Running Specific Tests

```bash
# Run a single test file
pytest tests/core/test_sync_engine.py

# Run a single test method
pytest tests/core/test_daily_summary.py::TestDailySummary::test_generate_basic_summary

# Run tests matching a pattern
pytest -k "test_format"

# Include TDD tests
pytest -m ""

# Debug test failures
pytest --pdb  # Drop into debugger on failure
pytest -x     # Stop on first failure
pytest --lf   # Run last failed tests
```

### Coverage Requirements

- Minimum coverage: 70%
- Core modules should have >90% coverage
- New features must include tests

View coverage report:
```bash
make test-cov
open htmlcov/index.html
```

### Windows Compatibility

All file operations must:
- Use `encoding='utf-8'` for text files
- Handle both `/` and `\` path separators
- Use `pathlib.Path` for path operations

### Test Structure

```python
class TestFeatureName:
    """Test suite for feature."""

    def test_happy_path(self):
        """Test normal expected behavior."""

    def test_edge_case(self):
        """Test boundary conditions."""

    def test_error_handling(self):
        """Test error scenarios."""
```

### Mocking

- Mock external services (Microsoft Graph API)
- Mock file system operations when possible
- Use fixtures for common test data

## Architecture Guidelines

### Adding New Features

1. **Core Features** go in `dayflow/core/`
2. **CLI Commands** go in `dayflow/ui/cli.py`
3. **Vault Operations** go in `dayflow/vault/`

### Dependencies

- Keep dependencies minimal
- Document why each dependency is needed
- Consider optional dependencies for advanced features

## Documentation

### Code Documentation

- Add docstrings to all public functions/classes
- Use Google-style docstrings:
  ```python
  def function(param1: str, param2: int) -> bool:
      """Short description.

      Longer description if needed.

      Args:
          param1: Description of param1
          param2: Description of param2

      Returns:
          Description of return value

      Raises:
          ValueError: When validation fails
      """
  ```

### User Documentation

- Update README.md for new commands
- Update ARCHITECTURE.md for new components
- Add examples to examples/ directory

## Setting up Codecov

To enable code coverage reporting:

1. Sign up at [codecov.io](https://codecov.io) with your GitHub account
2. Add your repository in Codecov
3. Copy your upload token
4. Add it to GitHub Secrets:
   - Go to Settings > Secrets and variables > Actions
   - Add secret named `CODECOV_TOKEN`
   - Paste your upload token

Note: CI is configured to not fail if Codecov upload fails.

## Release Process

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create release PR
4. Tag release after merge

## Questions?

- Open an issue for bugs or feature requests
- Start a discussion for questions
- Check existing issues before creating new ones

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive feedback
- Assume good intentions

Thank you for contributing!
