# Versioning Strategy for Dayflow

## Semantic Versioning

We follow [Semantic Versioning](https://semver.org/): **MAJOR.MINOR.PATCH**

- **MAJOR** (1.0.0): Breaking changes, incompatible API changes
- **MINOR** (0.1.0): New features, backwards compatible
- **PATCH** (0.1.1): Bug fixes, backwards compatible

## Version Management Options

### 1. Manual Version Control (Current Approach)
- Edit version in `pyproject.toml` manually
- Create tags manually: `git tag -a v0.1.1 -m "Bug fixes"`
- Best for: Controlled releases, clear milestones

### 2. Automated Patch Versions
Use `bump2version` or `python-semantic-release`:

```bash
# Install
pip install bump2version

# Create .bumpversion.cfg
[bumpversion]
current_version = 0.1.0
commit = True
tag = True

[bumpversion:file:pyproject.toml]
search = version = "{current_version}"
replace = version = "{new_version}"

[bumpversion:file:dayflow/__init__.py]

# Usage
bump2version patch  # 0.1.0 → 0.1.1
bump2version minor  # 0.1.1 → 0.2.0
bump2version major  # 0.2.0 → 1.0.0
```

### 3. Conventional Commits + Auto Release
Use conventional commits with automated releases:

```yaml
# .github/workflows/release.yml
name: Release
on:
  push:
    branches: [main]

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Python Semantic Release
        uses: python-semantic-release/python-semantic-release@master
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
```

Commit format triggers versions:
- `fix:` → patch (0.1.0 → 0.1.1)
- `feat:` → minor (0.1.1 → 0.2.0)
- `BREAKING CHANGE:` → major (0.2.0 → 1.0.0)

### 4. Git Flow with Release Branches
```bash
# Feature development
git checkout -b feature/new-feature
# ... work ...
git checkout develop
git merge feature/new-feature

# Release preparation
git checkout -b release/0.2.0
# Update version, changelog
git checkout main
git merge release/0.2.0
git tag -a v0.2.0
```

## Recommended Approach for Dayflow

### For Now (Manual Control):
1. Keep manual version control in `pyproject.toml`
2. Update version for each planned release
3. Tag releases manually
4. Use GitHub Releases for distribution

### Future Automation:
1. Set up `bump2version` for easier version updates
2. Use conventional commits
3. Add GitHub Action for automated releases
4. Consider calendar versioning (2025.1.0) for time-based releases

## Version Number Guidelines

- **0.x.y**: Pre-1.0, expect breaking changes
- **1.0.0**: First stable API
- **1.0.x**: Only bug fixes
- **1.x.0**: New features, no breaking changes
- **2.0.0**: Breaking changes

## Example Workflow

```bash
# After bug fixes
bump2version patch  # 0.1.0 → 0.1.1
git push origin main --tags

# After new features
bump2version minor  # 0.1.1 → 0.2.0
git push origin main --tags

# After breaking changes
bump2version major  # 0.2.0 → 1.0.0
git push origin main --tags
```
