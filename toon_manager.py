"""
Toon Manager - Context Management System

This module implements the "Toon" system referenced throughout the documentation.
Toons are named context snippets that provide reusable content for agent prompts.

Note: The underlying database table is named "Snippets" for implementation reasons,
but we expose it as "Toons" for consistency with documentation and conceptual model.

Toon Types:
- Summary: High-level summaries of large documents
- Chunk: Specific logical pieces of documents
- Instruction: Reusable instructions and guidelines
- Mapping: Saved successful mappings for automation (learning system)
- Version: Change descriptions and rationale
- Design: Design decision documentation
"""

from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# Toon Type Enum
# ============================================================================

class ToonType(str, Enum):
    """Types of Toons (context snippets)."""

    SUMMARY = "Summary"  # High-level summaries
    CHUNK = "Chunk"  # Document chunks
    INSTRUCTION = "Instruction"  # Reusable instructions
    MAPPING = "Mapping"  # Learned mappings (HITL feedback)
    VERSION = "Version"  # Version change descriptions
    DESIGN = "Design"  # Design decisions and rationale

    @classmethod
    def values(cls) -> List[str]:
        """Get list of valid values."""
        return [e.value for e in cls]


# ============================================================================
# Toon Data Class
# ============================================================================

@dataclass
class Toon:
    """Represents a Toon (named context snippet)."""

    toon_id: Optional[int]
    name: str
    toon_type: ToonType
    content: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'toon_id': self.toon_id,
            'name': self.name,
            'toon_type': self.toon_type.value if isinstance(self.toon_type, ToonType) else self.toon_type,
            'content': self.content,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Toon':
        """Create from dictionary (e.g., database row)."""
        return cls(
            toon_id=data.get('snippet_id') or data.get('toon_id'),  # Handle both names
            name=data.get('name'),
            toon_type=ToonType(data.get('snippet_type') or data.get('toon_type')),  # Handle both names
            content=data.get('content'),
            metadata=json.loads(data['metadata']) if isinstance(data.get('metadata'), str) else data.get('metadata'),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None,
        )


# ============================================================================
# Toon Manager Class
# ============================================================================

class ToonManager:
    """
    Manages Toons (context snippets) for agent prompt injection.

    This class provides the documented API for working with Toons,
    while transparently managing the underlying "Snippets" database table.
    """

    def __init__(self, db_manager):
        """
        Initialize ToonManager.

        Args:
            db_manager: DatabaseManager or SafeDatabaseManager instance
        """
        self.db = db_manager

    def create_toon(
        self,
        name: str,
        toon_type: ToonType,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a new Toon.

        Args:
            name: Unique name for the Toon
            toon_type: Type of Toon (use ToonType enum)
            content: Toon content
            metadata: Optional metadata dictionary

        Returns:
            int: ID of created Toon

        Example:
            >>> toon_id = toon_manager.create_toon(
            ...     name="OMOP_BP_Mapping",
            ...     toon_type=ToonType.MAPPING,
            ...     content="BP_SYST → OMOP:3004249 (Systolic BP)"
            ... )
        """
        # Convert ToonType enum to string if needed
        if isinstance(toon_type, ToonType):
            toon_type = toon_type.value

        # Validate toon_type
        if toon_type not in ToonType.values():
            raise ValueError(f"Invalid toon_type: {toon_type}. Must be one of {ToonType.values()}")

        # Serialize metadata
        metadata_json = json.dumps(metadata) if metadata else None

        # Insert into Snippets table (underlying storage)
        query = """
        INSERT INTO Snippets (name, snippet_type, content, metadata, created_at, updated_at)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """
        params = (name, toon_type, content, metadata_json)

        try:
            toon_id = self.db.execute_update(query, params)
            logger.info(f"✓ Created Toon: {name} (type: {toon_type}, id: {toon_id})")
            return toon_id
        except Exception as e:
            logger.error(f"✗ Failed to create Toon: {e}")
            raise

    def get_toon(self, toon_id: int) -> Optional[Toon]:
        """
        Get Toon by ID.

        Args:
            toon_id: Toon ID

        Returns:
            Toon object or None if not found
        """
        query = "SELECT * FROM Snippets WHERE snippet_id = ?"
        results = self.db.execute_query(query, (toon_id,))

        if results:
            return Toon.from_dict(results[0])
        return None

    def get_toon_by_name(self, name: str) -> Optional[Toon]:
        """
        Get Toon by name.

        Args:
            name: Toon name

        Returns:
            Toon object or None if not found

        Example:
            >>> toon = toon_manager.get_toon_by_name("OMOP_BP_Mapping")
        """
        query = "SELECT * FROM Snippets WHERE name = ?"
        results = self.db.execute_query(query, (name,))

        if results:
            return Toon.from_dict(results[0])
        return None

    def update_toon(
        self,
        toon_id: int,
        name: Optional[str] = None,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update an existing Toon.

        Args:
            toon_id: ID of Toon to update
            name: New name (optional)
            content: New content (optional)
            metadata: New metadata (optional)

        Returns:
            bool: True if successful

        Example:
            >>> toon_manager.update_toon(
            ...     toon_id=123,
            ...     content="Updated mapping: BP_SYST → OMOP:3004249"
            ... )
        """
        updates = []
        params = []

        if name is not None:
            updates.append("name = ?")
            params.append(name)

        if content is not None:
            updates.append("content = ?")
            params.append(content)

        if metadata is not None:
            updates.append("metadata = ?")
            params.append(json.dumps(metadata))

        if not updates:
            logger.warning("No fields to update")
            return False

        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(toon_id)

        query = f"UPDATE Snippets SET {', '.join(updates)} WHERE snippet_id = ?"

        try:
            self.db.execute_update(query, tuple(params))
            logger.info(f"✓ Updated Toon ID: {toon_id}")
            return True
        except Exception as e:
            logger.error(f"✗ Failed to update Toon: {e}")
            return False

    def delete_toon(self, toon_id: int) -> bool:
        """
        Delete a Toon.

        Args:
            toon_id: ID of Toon to delete

        Returns:
            bool: True if successful
        """
        query = "DELETE FROM Snippets WHERE snippet_id = ?"

        try:
            self.db.execute_update(query, (toon_id,))
            logger.info(f"✓ Deleted Toon ID: {toon_id}")
            return True
        except Exception as e:
            logger.error(f"✗ Failed to delete Toon: {e}")
            return False

    def list_toons(
        self,
        toon_type: Optional[ToonType] = None,
        limit: Optional[int] = None
    ) -> List[Toon]:
        """
        List all Toons, optionally filtered by type.

        Args:
            toon_type: Filter by Toon type (optional)
            limit: Maximum number to return (optional)

        Returns:
            List of Toon objects

        Example:
            >>> mappings = toon_manager.list_toons(toon_type=ToonType.MAPPING)
            >>> all_toons = toon_manager.list_toons()
        """
        if toon_type:
            if isinstance(toon_type, ToonType):
                toon_type = toon_type.value
            query = "SELECT * FROM Snippets WHERE snippet_type = ? ORDER BY created_at DESC"
            params = (toon_type,)
        else:
            query = "SELECT * FROM Snippets ORDER BY created_at DESC"
            params = ()

        if limit:
            query += f" LIMIT {limit}"

        results = self.db.execute_query(query, params)
        return [Toon.from_dict(row) for row in results]

    def search_toons(self, keyword: str, toon_type: Optional[ToonType] = None) -> List[Toon]:
        """
        Search Toons by keyword in name or content.

        Args:
            keyword: Search keyword
            toon_type: Filter by type (optional)

        Returns:
            List of matching Toons

        Example:
            >>> bp_toons = toon_manager.search_toons("blood pressure")
        """
        if toon_type:
            if isinstance(toon_type, ToonType):
                toon_type = toon_type.value
            query = """
            SELECT * FROM Snippets
            WHERE snippet_type = ? AND (name LIKE ? OR content LIKE ?)
            ORDER BY created_at DESC
            """
            keyword_pattern = f"%{keyword}%"
            params = (toon_type, keyword_pattern, keyword_pattern)
        else:
            query = """
            SELECT * FROM Snippets
            WHERE name LIKE ? OR content LIKE ?
            ORDER BY created_at DESC
            """
            keyword_pattern = f"%{keyword}%"
            params = (keyword_pattern, keyword_pattern)

        results = self.db.execute_query(query, params)
        return [Toon.from_dict(row) for row in results]

    def get_toons_for_injection(
        self,
        toon_types: List[ToonType],
        limit_per_type: int = 10
    ) -> List[Toon]:
        """
        Get Toons for agent context injection.

        Args:
            toon_types: List of Toon types to retrieve
            limit_per_type: Maximum Toons per type

        Returns:
            List of Toons suitable for prompt injection

        Example:
            >>> toons = toon_manager.get_toons_for_injection(
            ...     toon_types=[ToonType.INSTRUCTION, ToonType.MAPPING],
            ...     limit_per_type=5
            ... )
        """
        all_toons = []
        for toon_type in toon_types:
            toons = self.list_toons(toon_type=toon_type, limit=limit_per_type)
            all_toons.extend(toons)

        return all_toons

    def create_mapping_from_hitl(
        self,
        field_name: str,
        ontology_mapping: str,
        source_job_id: Optional[str] = None
    ) -> int:
        """
        Create a Mapping Toon from HITL feedback (learning system).

        This enables the system to learn from human corrections.

        Args:
            field_name: Field that was mapped
            ontology_mapping: The approved mapping
            source_job_id: Job where this was learned (optional)

        Returns:
            int: ID of created Mapping Toon

        Example:
            >>> toon_id = toon_manager.create_mapping_from_hitl(
            ...     field_name="BP_SYST",
            ...     ontology_mapping="OMOP:3004249 (Systolic Blood Pressure)"
            ... )
        """
        name = f"Mapping_{field_name}"
        content = f"{field_name} → {ontology_mapping}"
        metadata = {
            'field_name': field_name,
            'mapping': ontology_mapping,
            'source': 'human_review',
            'source_job_id': source_job_id,
            'learned_at': datetime.now().isoformat()
        }

        return self.create_toon(
            name=name,
            toon_type=ToonType.MAPPING,
            content=content,
            metadata=metadata
        )

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about Toons in the system.

        Returns:
            Dictionary with statistics
        """
        stats = {
            'total_toons': 0,
            'by_type': {}
        }

        # Total count
        total_result = self.db.execute_query("SELECT COUNT(*) as count FROM Snippets")
        stats['total_toons'] = total_result[0]['count'] if total_result else 0

        # Count by type
        for toon_type in ToonType:
            type_result = self.db.execute_query(
                "SELECT COUNT(*) as count FROM Snippets WHERE snippet_type = ?",
                (toon_type.value,)
            )
            stats['by_type'][toon_type.value] = type_result[0]['count'] if type_result else 0

        return stats


# ============================================================================
# Toon Notation Encoding/Decoding (for compact data representation)
# ============================================================================

class ToonNotation:
    """
    Toon notation for compact data encoding (40-70% token reduction).

    Converts verbose JSON to compact tabular format.
    """

    @staticmethod
    def encode(data: Dict[str, Any]) -> str:
        """
        Encode data to Toon notation.

        Example:
            Input: {"items": [{"id": 1, "qty": 5}, {"id": 2, "qty": 3}]}
            Output:
                items[2]{id,qty}:
                  1,5
                  2,3

        Args:
            data: Dictionary to encode

        Returns:
            Compact Toon notation string
        """
        # This is a simplified implementation
        # Full implementation would handle nested structures
        lines = []

        for key, value in data.items():
            if isinstance(value, list) and value and isinstance(value[0], dict):
                # Array of objects - use tabular format
                fields = list(value[0].keys())
                lines.append(f"{key}[{len(value)}]{{{','.join(fields)}}}:")

                for item in value:
                    values = [str(item.get(f, '')) for f in fields]
                    lines.append(f"  {','.join(values)}")
            elif isinstance(value, list):
                # Simple array
                lines.append(f"{key}: {','.join(map(str, value))}")
            else:
                # Simple value
                lines.append(f"{key}: {value}")

        return '\n'.join(lines)

    @staticmethod
    def decode(notation: str) -> Dict[str, Any]:
        """
        Decode Toon notation back to dictionary.

        Args:
            notation: Toon notation string

        Returns:
            Decoded dictionary
        """
        # Simplified decoder - full implementation would handle all cases
        result = {}
        current_array = None
        current_fields = None

        for line in notation.split('\n'):
            line = line.strip()
            if not line:
                continue

            if '[' in line and '{' in line:
                # Array declaration
                parts = line.split('[')
                key = parts[0]
                fields_part = line.split('{')[1].split('}')[0]
                current_array = key
                current_fields = fields_part.split(',')
                result[current_array] = []
            elif current_array and line.startswith((' ', '\t')):
                # Array data row
                values = line.strip().split(',')
                item = dict(zip(current_fields, values))
                result[current_array].append(item)
            elif ':' in line:
                # Simple key-value
                key, value = line.split(':', 1)
                result[key.strip()] = value.strip()

        return result

