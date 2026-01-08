import json
import logging
from typing import List, Dict, Optional
from .database import DatabaseManager
from .models import Snippet, SnippetType
from .utils.formatters import ToonNotation

logger = logging.getLogger('ADE.SnippetManager')

class SnippetManager:
    """Manages the Snippet Library for named context storage and retrieval."""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        # Schema is handled by DatabaseManager.initialize_schema
        # But we might need to handle migration if needed, 
        # but for fresh install DatabaseManager does it.

    def create_snippet(self, name: str, snippet_type: SnippetType, content: str,
                      metadata: Optional[Dict] = None) -> int:
        """Create a new snippet in the library."""
        query = """
        INSERT INTO Snippets (name, snippet_type, content, metadata)
        VALUES (?, ?, ?, ?)
        """
        metadata_json = json.dumps(metadata) if metadata else None
        snippet_id = self.db.execute_update(query, (name, snippet_type.value, content, metadata_json))
        logger.info(f"Created Snippet '{name}' (ID: {snippet_id})")
        return snippet_id

    def get_snippet_by_name(self, name: str) -> Optional[Snippet]:
        """Retrieve a snippet by name."""
        query = "SELECT * FROM Snippets WHERE name = ?"
        result = self.db.execute_query(query, (name,))
        if result:
            row = result[0]
            return Snippet(
                snippet_id=row['snippet_id'],
                name=row['name'],
                snippet_type=SnippetType(row['snippet_type']),
                content=row['content'],
                metadata=json.loads(row['metadata']) if row['metadata'] else None
            )
        return None

    def update_snippet(self, snippet_id: int, content: str = None, metadata: Dict = None):
        """Update an existing snippet."""
        if content:
            self.db.execute_update(
                "UPDATE Snippets SET content = ?, updated_at = CURRENT_TIMESTAMP WHERE snippet_id = ?",
                (content, snippet_id)
            )
        if metadata:
            self.db.execute_update(
                "UPDATE Snippets SET metadata = ?, updated_at = CURRENT_TIMESTAMP WHERE snippet_id = ?",
                (json.dumps(metadata), snippet_id)
            )

    def list_snippets(self, snippet_type: Optional[SnippetType] = None) -> List[Snippet]:
        """List all snippets, optionally filtered by type."""
        if snippet_type:
            query = "SELECT * FROM Snippets WHERE snippet_type = ?"
            results = self.db.execute_query(query, (snippet_type.value,))
        else:
            query = "SELECT * FROM Snippets"
            results = self.db.execute_query(query)

        return [
            Snippet(
                snippet_id=row['snippet_id'],
                name=row['name'],
                snippet_type=SnippetType(row['snippet_type']),
                content=row['content'],
                metadata=json.loads(row['metadata']) if row['metadata'] else None
            )
            for row in results
        ]

    def delete_snippet(self, snippet_id: int):
        """Delete a snippet from the library."""
        self.db.execute_update("DELETE FROM Snippets WHERE snippet_id = ?", (snippet_id,))
        logger.info(f"Deleted Snippet ID: {snippet_id}")

    def create_convention_snippet(self, name: str, convention_rules: Dict) -> int:
        """Create a snippet specifically for data conventions."""
        content = ToonNotation.encode(convention_rules)
        return self.create_snippet(
            name=name,
            snippet_type=SnippetType.CONVENTION,
            content=content,
            metadata={"type": "naming_conventions", "auto_generated": False}
        )

    def create_changelog_snippet(self, name: str, changes: List[Dict]) -> int:
        """Create a snippet for version changelog."""
        content = ToonNotation.encode({"changes": changes})
        return self.create_snippet(
            name=name,
            snippet_type=SnippetType.CHANGELOG,
            content=content,
            metadata={"type": "version_history", "entries": len(changes)}
        )

    def create_instrument_snippet(self, name: str, instrument_data: Dict) -> int:
        """Create a snippet for instrument documentation."""
        content = ToonNotation.encode(instrument_data)
        return self.create_snippet(
            name=name,
            snippet_type=SnippetType.INSTRUMENT,
            content=content,
            metadata={"type": "instrument", "variable_count": len(instrument_data.get("variables", []))}
        )
