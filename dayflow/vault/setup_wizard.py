"""
Interactive setup wizard for vault configuration.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import click

from .config import VaultConfig
from .detector import VaultDetector, VaultStructure


@dataclass
class SetupChoice:
    """Represents a setup choice."""

    display: str
    value: str
    exists: bool = True
    description: str = ""


class VaultSetupWizard:
    """Interactive wizard for vault setup."""

    def __init__(self):
        self.detector = VaultDetector()
        self.config = VaultConfig()
        self.vault_path: Optional[Path] = None
        self.structure: Optional[VaultStructure] = None

    def run(self) -> bool:
        """Run the interactive setup wizard.

        Returns:
            True if setup completed successfully
        """
        click.clear()
        click.echo("🏗️  Dayflow - Vault Setup Wizard")
        click.echo("=" * 60)
        click.echo()

        # Step 1: Find or select vault
        if not self._select_vault():
            return False

        # Step 2: Analyze structure
        self._analyze_structure()

        # Step 3: Configure locations
        if not self._configure_locations():
            return False

        # Step 4: Preview and confirm
        if not self._preview_and_confirm():
            return False

        # Step 5: Save configuration
        self._save_configuration()

        # Step 6: Optional test
        self._offer_test()

        return True

    def _select_vault(self) -> bool:
        """Select Obsidian vault."""
        click.echo("📁 Step 1: Select your Obsidian vault")
        click.echo("-" * 40)

        # Search for vaults
        vaults = self.detector.find_obsidian_vaults()

        choices = []
        if vaults:
            click.echo(f"\nFound {len(vaults)} Obsidian vault(s):\n")
            for i, vault in enumerate(vaults, 1):
                # Get some stats about the vault
                stats = self.detector.get_vault_stats(vault)
                notes = stats.get("total_notes", 0)
                click.echo(f"  {i}. {vault.name}")
                click.echo(f"     📍 {vault}")
                click.echo(f"     📝 {notes} notes")
                choices.append(vault)

        # Add manual entry option
        choices.append("manual")
        click.echo(f"\n  {len(choices)}. Enter path manually")
        click.echo("  0. Cancel setup")

        # Get choice
        while True:
            try:
                choice = click.prompt("\nSelect option", type=int)
                if choice == 0:
                    click.echo("Setup cancelled.")
                    return False
                elif 1 <= choice < len(choices):
                    self.vault_path = choices[choice - 1]
                    break
                elif choice == len(choices):
                    # Manual entry
                    path = click.prompt("Enter vault path")
                    path = Path(path).expanduser().resolve()
                    if not path.exists():
                        if click.confirm("Path doesn't exist. Create it?"):
                            path.mkdir(parents=True)
                        else:
                            continue
                    self.vault_path = path
                    break
                else:
                    click.echo("Invalid choice. Please try again.")
            except (ValueError, EOFError):
                click.echo("Invalid input. Please enter a number.")

        # Validate it's an Obsidian vault
        if self.vault_path and not (self.vault_path / ".obsidian").exists():
            click.echo(
                f"\n⚠️  '{self.vault_path}' doesn't appear to be an Obsidian vault."
            )
            if not click.confirm("Continue anyway?"):
                return False

        click.echo(f"\n✅ Selected vault: {self.vault_path}")
        return True

    def _analyze_structure(self):
        """Analyze vault structure."""
        click.echo("\n📊 Step 2: Analyzing vault structure")
        click.echo("-" * 40)

        self.structure = self.detector.analyze_vault(self.vault_path)

        if self.structure.is_empty:
            click.echo("📭 Vault is empty - will use default structure")
        else:
            click.echo(f"🔍 Detected structure: {self.structure.type.upper()}")

            # Show existing folders
            folders = [
                f
                for f in self.vault_path.iterdir()
                if f.is_dir() and not f.name.startswith(".")
            ]
            if folders:
                click.echo("\nExisting folders:")
                for folder in sorted(folders)[:10]:
                    click.echo(f"  📁 {folder.name}")
                if len(folders) > 10:
                    click.echo(f"  ... and {len(folders) - 10} more")

    def _configure_locations(self) -> bool:
        """Configure where different content types go."""
        click.echo("\n⚙️  Step 3: Configure locations")
        click.echo("-" * 40)

        # Location types to configure
        location_configs: List[Dict[str, Any]] = [
            {
                "type": "calendar_events",
                "name": "Calendar Events",
                "description": "Where to save synced calendar meetings",
                "suggestions": self._suggest_calendar_location(),
                "default": "Calendar Events",
            },
            {
                "type": "daily_notes",
                "name": "Daily Notes",
                "description": "Where to save daily summary notes (optional)",
                "suggestions": self._suggest_daily_location(),
                "default": "Daily Notes",
                "optional": True,
            },
        ]

        locations = {}

        for loc_config in location_configs:
            click.echo(f"\n📍 {loc_config['name']}")
            click.echo(f"   {loc_config['description']}")

            # Show suggestions
            choices = []
            if loc_config["suggestions"]:
                click.echo("\n   Suggested locations:")
                for i, (path, exists) in enumerate(loc_config["suggestions"], 1):
                    status = "✅ exists" if exists else "🆕 will create"
                    click.echo(f"   {i}. {path} ({status})")
                    choices.append(path)

            # Add custom option
            choices.append("custom")
            click.echo(f"   {len(choices)}. Enter custom path")

            if loc_config.get("optional"):
                choices.append("skip")
                click.echo(f"   {len(choices)}. Skip (don't configure)")

            # Get choice
            while True:
                try:
                    choice = click.prompt(
                        f"\n   Select location for {loc_config['name']}",
                        type=int,
                        default=1,
                    )
                    if 1 <= choice <= len(choices):
                        selected = choices[choice - 1]
                        if selected == "custom":
                            custom_path = click.prompt("   Enter folder path")
                            locations[loc_config["type"]] = custom_path
                        elif selected == "skip":
                            # Skip this location
                            pass
                        else:
                            locations[loc_config["type"]] = selected
                        break
                    else:
                        click.echo("   Invalid choice. Please try again.")
                except (ValueError, EOFError):
                    click.echo("   Invalid input. Please enter a number.")

            # Show what was selected
            if loc_config["type"] in locations:
                full_path = self.vault_path / locations[loc_config["type"]]
                if full_path.exists():
                    click.echo(f"   ✅ Will use: {locations[loc_config['type']]}")
                else:
                    click.echo(f"   🆕 Will create: {locations[loc_config['type']]}")

        self.locations = locations
        return True

    def _suggest_calendar_location(self) -> List[Tuple[str, bool]]:
        """Suggest locations for calendar events."""
        suggestions = []

        # Check for existing meeting-related folders
        if self.vault_path:
            for folder in self.vault_path.iterdir():
                if folder.is_dir() and not folder.name.startswith("."):
                    lower_name = folder.name.lower()
                    if any(
                        word in lower_name
                        for word in ["meeting", "calendar", "event", "work"]
                    ):
                        suggestions.append((folder.name, True))

        # Add structure-specific suggestions
        if self.structure:
            suggested = self.structure.get_location("calendar_events")
            path = Path(suggested)
            exists = bool(self.vault_path and (self.vault_path / path).exists())
            if suggested not in [s[0] for s in suggestions]:
                suggestions.append((suggested, exists))

        # Add default if nothing found
        if not suggestions:
            suggestions.append(("Calendar Events", False))
            suggestions.append(("Meetings", False))

        return suggestions[:3]  # Limit to 3 suggestions

    def _suggest_daily_location(self) -> List[Tuple[str, bool]]:
        """Suggest locations for daily notes."""
        suggestions = []

        # Check for existing daily-related folders
        if self.vault_path:
            for folder in self.vault_path.iterdir():
                if folder.is_dir() and not folder.name.startswith("."):
                    lower_name = folder.name.lower()
                    if any(
                        word in lower_name for word in ["daily", "journal", "diary"]
                    ):
                        suggestions.append((folder.name, True))

        # Add structure-specific suggestions
        if self.structure:
            suggested = self.structure.get_location("daily_notes")
            path = Path(suggested)
            exists = bool(self.vault_path and (self.vault_path / path).exists())
            if suggested not in [s[0] for s in suggestions]:
                suggestions.append((suggested, exists))

        # Add default
        if not suggestions:
            suggestions.append(("Daily Notes", False))

        return suggestions[:3]

    def _preview_and_confirm(self) -> bool:
        """Preview configuration and confirm."""
        click.echo("\n👀 Step 4: Review configuration")
        click.echo("-" * 40)

        click.echo(f"\nVault: {self.vault_path}")
        click.echo("\nLocations:")

        for loc_type, loc_path in self.locations.items():
            full_path = self.vault_path / loc_path
            status = "✅" if full_path.exists() else "🆕"
            click.echo(f"  {status} {loc_type}: {loc_path}")

        # Show example paths
        click.echo("\nExample file paths:")
        if "calendar_events" in self.locations:
            example = (
                self.vault_path
                / self.locations["calendar_events"]
                / "2024-01-15 Team Meeting.md"
            )
            click.echo(f"  📅 {example}")

        return bool(click.confirm("\nSave this configuration?"))

    def _save_configuration(self):
        """Save the configuration."""
        click.echo("\n💾 Step 5: Saving configuration")
        click.echo("-" * 40)

        # Set vault path
        self.config.set_vault_path(str(self.vault_path))

        # Set locations
        for loc_type, loc_path in self.locations.items():
            self.config.set_location(loc_type, loc_path)

        # Create folders
        for loc_type, loc_path in self.locations.items():
            full_path = self.vault_path / loc_path
            if not full_path.exists():
                full_path.mkdir(parents=True)
                click.echo(f"  📁 Created: {loc_path}")

        click.echo(f"\n✅ Configuration saved to: {self.config.config_path}")

    def _offer_test(self):
        """Offer to verify the setup."""
        click.echo("\n🧪 Step 6: Verify setup")
        click.echo("-" * 40)

        click.echo("\nYour vault is now configured!")
        click.echo("\nTo verify the setup is working:")
        click.echo("1. Run: dayflow sync")
        click.echo("2. Check your vault for synchronized calendar events")
        click.echo("\nNote: You'll need to authenticate first with: dayflow auth login")
