# Contributing to Dayflow

Thank you for your interest in contributing to Dayflow!

## Getting Started

### Development Setup

1. Fork and clone the repository:
   ```bash
   git clone https://github.com/malathon/dayflow.git
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

### Running Tests

```bash
# Run all tests
make test

# Run specific test files
pytest tests/test_meeting_matcher.py

# Run with coverage
make test-cov

# Run only new feature tests
make test-new
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
