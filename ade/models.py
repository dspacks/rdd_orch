from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from enum import Enum
import json

class SnippetType(Enum):
    """Enumeration of snippet types for context management."""
    SUMMARY = "Summary"
    CHUNK = "Chunk"
    INSTRUCTION = "Instruction"
    VERSION = "Version"
    DESIGN = "Design"
    MAPPING = "Mapping"
    # Extended snippet types for new agents
    CONVENTION = "Convention"        # Data naming conventions and standards
    CHANGELOG = "Changelog"          # Version history and change logs
    INSTRUMENT = "Instrument"        # Higher-level instrument documentation
    SEGMENT = "Segment"              # Codebook segment documentation
    GLOSSARY = "Glossary"            # Conventions glossary

@dataclass
class Snippet:
    """Represents a named context snippet."""
    name: str
    snippet_type: SnippetType
    content: str
    metadata: Optional[Dict[str, Any]] = None
    snippet_id: Optional[int] = None

@dataclass
class ReviewItem:
    """Represents an item in the review queue."""
    item_id: int
    job_id: str
    status: str
    source_agent: str
    generated_content: str
    source_data: str
    target_agent: Optional[str] = None
    approved_content: Optional[str] = None
    rejection_feedback: Optional[str] = None
    clarification_response: Optional[str] = None

@dataclass
class ProcessingCheckpoint:
    """Represents a checkpoint in the processing pipeline."""
    job_id: str
    checkpoint_time: str
    stage: str  # 'parsed', 'analyzed', 'ontology', 'documented'
    variables_processed: int
    total_variables: int
    parsed_data: Optional[List[Dict]] = None
    analyzed_data: Optional[List[Dict]] = None
    processed_variables: Optional[List[str]] = None
    checkpoint_file: Optional[str] = None
