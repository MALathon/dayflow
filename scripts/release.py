#!/usr/bin/env python3
"""Release automation script for Dayflow.

This script automates the release process:
1. Updates version numbers
2. Updates CHANGELOG.md
3. Creates git tag
4. Creates GitHub release
"""

import argparse
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def run_command(cmd, capture_output=False):
    """Run a shell command and handle errors."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=capture_output, text=True)
    if result.returncode != 0:
        print(f"Error running command: {cmd}")
        if result.stderr:
            print(f"Error: {result.stderr}")
        sys.exit(1)
    return result.stdout if capture_output else None


def get_current_version():
    """Get current version from pyproject.toml."""
    pyproject = Path("pyproject.toml").read_text()
    match = re.search(r'version = "([^"]+)"', pyproject)
    if not match:
        print("Could not find version in pyproject.toml")
        sys.exit(1)
    return match.group(1)


def update_version(new_version):
    """Update version in pyproject.toml and __init__.py."""
    # Update pyproject.toml
    pyproject_path = Path("pyproject.toml")
    content = pyproject_path.read_text()
    content = re.sub(r'version = "[^"]+"', f'version = "{new_version}"', content)
    pyproject_path.write_text(content)

    # Update __init__.py
    init_path = Path("dayflow/__init__.py")
    content = init_path.read_text()
    content = re.sub(
        r'__version__ = "[^"]+"', f'__version__ = "{new_version}"', content
    )
    init_path.write_text(content)

    print(f"Updated version to {new_version}")


def update_changelog(version):
    """Update CHANGELOG.md - move Unreleased to new version."""
    changelog_path = Path("CHANGELOG.md")
    content = changelog_path.read_text()

    today = datetime.now().strftime("%Y-%m-%d")

    # Check if there's an Unreleased section with content
    if "## [Unreleased]" not in content:
        print("No [Unreleased] section found in CHANGELOG.md")
        sys.exit(1)

    # Replace [Unreleased] with new version
    new_section = f"## [Unreleased]\n\n## [{version}] - {today}"
    content = content.replace("## [Unreleased]", new_section)

    changelog_path.write_text(content)
    print(f"Updated CHANGELOG.md with version {version}")


def extract_release_notes(version):
    """Extract release notes for specific version from CHANGELOG."""
    changelog = Path("CHANGELOG.md").read_text()

    # Find the section for this version
    pattern = rf"## \[{re.escape(version)}\].*?(?=## \[|$)"
    match = re.search(pattern, changelog, re.DOTALL)

    if not match:
        print(f"Could not find release notes for version {version}")
        sys.exit(1)

    # Clean up the notes (remove the version header)
    notes = match.group(0)
    notes = re.sub(r"## \[[^\]]+\][^\n]*\n", "", notes).strip()

    # Save to temp file
    temp_file = Path("/tmp/release_notes.md")
    temp_file.write_text(f"# Dayflow v{version} Release Notes\n\n{notes}")

    return temp_file


def create_release(version, draft=False):
    """Create git tag and GitHub release."""
    # Ensure we're on main branch
    current_branch = run_command("git branch --show-current", capture_output=True)
    if current_branch:
        current_branch = current_branch.strip()
    if current_branch != "main":
        print(f"Error: Must be on main branch (currently on {current_branch})")
        sys.exit(1)

    # Ensure working directory is clean
    status = run_command("git status --porcelain", capture_output=True)
    if status:
        print("Error: Working directory has uncommitted changes")
        print("Please commit or stash changes before releasing")
        sys.exit(1)

    # Pull latest changes
    run_command("git pull origin main")

    # Update version
    update_version(version)

    # Update CHANGELOG
    update_changelog(version)

    # Commit changes
    run_command("git add pyproject.toml dayflow/__init__.py CHANGELOG.md")
    run_command(f'git commit -m "chore: Release version {version}"')

    # Create tag
    release_notes = extract_release_notes(version)
    run_command(f"git tag -a v{version} -F {release_notes}")

    # Push changes and tag
    run_command("git push origin main")
    run_command(f"git push origin v{version}")

    # Create GitHub release
    draft_flag = "--draft" if draft else ""
    run_command(
        f"gh release create v{version} "
        f'--title "Dayflow v{version}" '
        f"--notes-file {release_notes} "
        f"{draft_flag}"
    )

    print(f"\n✅ Successfully released version {version}!")
    print(f"View release: https://github.com/MALathon/dayflow/releases/tag/v{version}")


def main():
    parser = argparse.ArgumentParser(
        description="Automate Dayflow releases",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/release.py 0.3.0
  python scripts/release.py 0.3.0 --draft
  python scripts/release.py --check
""",
    )

    parser.add_argument("version", nargs="?", help="New version number (e.g., 0.3.0)")
    parser.add_argument("--draft", action="store_true", help="Create a draft release")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check current version and unreleased changes",
    )

    args = parser.parse_args()

    if args.check:
        current = get_current_version()
        print(f"Current version: {current}")

        # Check for unreleased changes
        changelog = Path("CHANGELOG.md").read_text()
        unreleased_match = re.search(
            r"## \[Unreleased\](.+?)(?=## \[|$)", changelog, re.DOTALL
        )
        if unreleased_match and unreleased_match.group(1).strip():
            print("\nUnreleased changes found in CHANGELOG.md")
        else:
            print("\nNo unreleased changes in CHANGELOG.md")
        return

    if not args.version:
        parser.error("Version number required (unless using --check)")

    # Validate version format
    if not re.match(r"^\d+\.\d+\.\d+$", args.version):
        print(f"Error: Invalid version format '{args.version}'")
        print("Expected format: X.Y.Z (e.g., 0.3.0)")
        sys.exit(1)

    create_release(args.version, args.draft)


if __name__ == "__main__":
    main()
