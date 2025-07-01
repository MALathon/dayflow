"""
Zettelkasten system implementation.
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from dayflow.vault import VaultConfig, VaultConnection


class ZettelkastenEngine:
    """Manages Zettelkasten note system in Obsidian vault."""

    def __init__(self, vault_connection: Optional[VaultConnection] = None):
        """Initialize Zettelkasten engine.

        Args:
            vault_connection: Connection to vault for note operations
        """
        self.vault_connection = vault_connection
        self.config = VaultConfig() if vault_connection else None

    def generate_id(self) -> str:
        """Generate unique Zettel ID.

        Returns:
            Timestamp-based ID in format YYYYMMDDHHmmss
        """
        return datetime.now().strftime("%Y%m%d%H%M%S")

    def create_zettel(
        self,
        title: str,
        content: str,
        zettel_type: str = "permanent",
        tags: Optional[List[str]] = None,
        references: Optional[List[str]] = None,
    ) -> Path:
        """Create a new Zettelkasten note.

        Args:
            title: Note title
            content: Note content
            zettel_type: Type of note (permanent, literature, fleeting)
            tags: Optional list of tags
            references: Optional list of referenced note IDs

        Returns:
            Path to created note
        """
        if not self.vault_connection:
            raise ValueError("No vault connection configured")

        zettel_id = self.generate_id()
        timestamp = datetime.now()

        # Build frontmatter
        frontmatter_lines = [
            "---",
            f"id: {zettel_id}",
            f"title: {title}",
            f"created: {timestamp.isoformat()}",
            f"type: {zettel_type}",
        ]

        if tags:
            frontmatter_lines.append(f"tags: {tags}")

        if references:
            frontmatter_lines.append(f"references: {references}")

        frontmatter_lines.append("---")

        # Build note content
        note_content = "\n".join(frontmatter_lines) + f"\n\n# {title}\n\n{content}\n"

        # Add reference links
        if references:
            note_content += "\n## References\n"
            for ref in references:
                note_content += f"- [[{ref}]]\n"

        # Generate filename
        safe_title = title[:50].replace("/", "-").replace(":", "-")
        filename = f"{zettel_id} {safe_title}.md"

        # Determine location based on type
        location_map = {
            "permanent": "zettel_permanent",
            "literature": "zettel_literature",
            "fleeting": "zettel_fleeting",
        }
        location = location_map.get(zettel_type, "zettel_permanent")

        # Write note
        return self.vault_connection.write_note(note_content, filename, location)

    def find_unprocessed_literature_notes(self) -> List[Path]:
        """Find literature notes that haven't been processed into permanent notes.

        Returns:
            List of paths to unprocessed literature notes
        """
        if not self.vault_connection:
            return []

        lit_path = self.config.get_location("zettel_literature")
        if not lit_path or not lit_path.exists():
            return []

        unprocessed = []

        # Simple heuristic: literature notes without "processed" tag
        for file in lit_path.glob("*.md"):
            content = file.read_text()
            if "processed: true" not in content and "#processed" not in content:
                unprocessed.append(file)

        return sorted(unprocessed)

    def suggest_permanent_notes(self, literature_note_path: Path) -> List[Dict]:
        """Suggest permanent notes based on a literature note.

        Args:
            literature_note_path: Path to literature note

        Returns:
            List of suggested permanent notes with titles and reasons
        """
        if not literature_note_path.exists():
            return []

        content = literature_note_path.read_text()
        suggestions = []

        # Extract key concepts (simplified - looks for headers and bold text)
        headers = re.findall(r"^#{1,3}\s+(.+)$", content, re.MULTILINE)
        bold_text = re.findall(r"\*\*(.+?)\*\*", content)

        # Generate suggestions based on extracted concepts
        for header in headers[:3]:  # Limit to first 3 headers
            if len(header) > 10:  # Skip very short headers
                suggestions.append(
                    {"title": header, "reason": "Key section in literature note"}
                )

        for bold in bold_text[:2]:  # Limit to first 2 bold items
            if len(bold) > 10:
                suggestions.append({"title": bold, "reason": "Emphasized concept"})

        return suggestions

    def create_literature_note(
        self,
        title: str,
        source: str,
        author: Optional[str] = None,
        content: str = "",
        tags: Optional[List[str]] = None,
    ) -> Path:
        """Create a literature note from a source.

        Args:
            title: Note title
            source: Source of the literature (book, article, etc.)
            author: Optional author name
            content: Initial content
            tags: Optional tags

        Returns:
            Path to created note
        """
        # Build content with source info
        full_content = f"## Source\n- Title: {source}\n"
        if author:
            full_content += f"- Author: {author}\n"
        full_content += f"\n## Notes\n{content}"

        # Add literature-specific tags
        if tags is None:
            tags = []
        tags.extend(["literature-note", "unprocessed"])

        return self.create_zettel(
            title=title, content=full_content, zettel_type="literature", tags=tags
        )

    def search_zettels(self, query: str) -> List[Tuple[Path, str]]:
        """Search for zettels matching query.

        Args:
            query: Search query

        Returns:
            List of (path, matching_line) tuples
        """
        if not self.vault_connection:
            return []

        results = []

        # Search in all zettel locations
        for location in ["zettel_permanent", "zettel_literature", "zettel_fleeting"]:
            loc_path = self.config.get_location(location)
            if loc_path and loc_path.exists():
                for file in loc_path.glob("*.md"):
                    content = file.read_text()
                    if query.lower() in content.lower():
                        # Find the matching line
                        for line in content.split("\n"):
                            if query.lower() in line.lower():
                                results.append((file, line.strip()))
                                break

        return results
