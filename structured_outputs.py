"""
Pydantic models for structured agent outputs.

Provides type-safe, validated data structures for all agent responses.
This improves reliability by catching malformed LLM outputs early.
"""

from typing import Dict, List, Optional, Any, Literal
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from enum import Enum


# ============================================================================
# Enums
# ============================================================================

class ConfidenceLevel(str, Enum):
    """Confidence levels for agent outputs."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNCERTAIN = "uncertain"


class ReviewStatus(str, Enum):
    """Status values for review queue items."""
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    NEEDS_CLARIFICATION = "Needs_Clarification"


class JobStatus(str, Enum):
    """Status values for processing jobs."""
    RUNNING = "Running"
    COMPLETED = "Completed"
    FAILED = "Failed"
    PAUSED = "Paused"


# ============================================================================
# Base Agent Output
# ============================================================================

class BaseAgentOutput(BaseModel):
    """Base structure for all agent outputs."""

    content: str = Field(..., min_length=1, description="Primary output content")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence score (0.0-1.0)")
    confidence_level: Optional[ConfidenceLevel] = Field(default=None, description="Categorical confidence")
    needs_human_review: bool = Field(default=False, description="Flag for HITL routing")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    warnings: List[str] = Field(default_factory=list, description="Non-critical warnings")
    errors: List[str] = Field(default_factory=list, description="Critical errors")

    @field_validator('confidence_level', mode='before')
    @classmethod
    def set_confidence_level(cls, v, info):
        """Automatically set confidence_level from confidence score if not provided."""
        if v is None and 'confidence' in info.data:
            conf = info.data['confidence']
            if conf >= 0.8:
                return ConfidenceLevel.HIGH
            elif conf >= 0.6:
                return ConfidenceLevel.MEDIUM
            elif conf >= 0.3:
                return ConfidenceLevel.LOW
            else:
                return ConfidenceLevel.UNCERTAIN
        return v


# ============================================================================
# Data Parser Agent Output
# ============================================================================

class ParsedField(BaseModel):
    """Individual field parsed from data dictionary."""

    field_name: str = Field(..., description="Variable/field name")
    field_type: Optional[str] = Field(None, description="Data type (integer, text, radio, etc.)")
    field_label: Optional[str] = Field(None, description="Human-readable label")
    choices: Optional[str] = Field(None, description="Choice options (for categorical fields)")
    notes: Optional[str] = Field(None, description="Additional notes/description")
    required: Optional[bool] = Field(None, description="Is field required?")
    validation: Optional[Dict[str, Any]] = Field(None, description="Validation rules")


class DataParserOutput(BaseAgentOutput):
    """Output from DataParserAgent."""

    fields: List[ParsedField] = Field(default_factory=list, description="Parsed fields")
    total_fields: int = Field(default=0, description="Total number of fields parsed")
    source_format: Optional[str] = Field(None, description="Detected source format (CSV, XML, JSON, etc.)")


# ============================================================================
# Technical Analyzer Output
# ============================================================================

class TechnicalAnalysis(BaseModel):
    """Technical analysis for a single field."""

    field_name: str
    inferred_type: str = Field(..., description="Inferred data type")
    cardinality: str = Field(..., description="required, optional, or multi-valued")
    constraints: Dict[str, Any] = Field(default_factory=dict, description="Data constraints")
    valid_values: Optional[List[Any]] = Field(None, description="Enumerated valid values")
    pattern: Optional[str] = Field(None, description="Regex pattern if applicable")


class TechnicalAnalyzerOutput(BaseAgentOutput):
    """Output from TechnicalAnalyzerAgent."""

    analyses: List[TechnicalAnalysis] = Field(default_factory=list, description="Field analyses")
    naming_convention: Optional[str] = Field(None, description="Detected naming convention")
    convention_compliance: Optional[float] = Field(None, ge=0.0, le=1.0, description="Convention compliance score")


# ============================================================================
# Domain Ontology Mapping Output
# ============================================================================

class OntologyMapping(BaseModel):
    """Ontology mapping for a field."""

    field_name: str
    ontology_type: str = Field(..., description="OMOP, LOINC, SNOMED, RxNorm, etc.")
    concept_id: str = Field(..., description="Concept ID in the ontology")
    concept_name: str = Field(..., description="Human-readable concept name")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Mapping confidence")
    alternative_mappings: List[Dict[str, Any]] = Field(default_factory=list, description="Alternative options")


class DomainOntologyOutput(BaseAgentOutput):
    """Output from DomainOntologyAgent."""

    mappings: List[OntologyMapping] = Field(default_factory=list, description="Ontology mappings")
    unmapped_fields: List[str] = Field(default_factory=list, description="Fields without mappings")
    mapping_coverage: Optional[float] = Field(None, ge=0.0, le=1.0, description="Percentage of fields mapped")


# ============================================================================
# Plain Language Documentation Output
# ============================================================================

class FieldDocumentation(BaseModel):
    """Plain language documentation for a field."""

    field_name: str
    description: str = Field(..., min_length=10, description="Human-readable description")
    clinical_context: Optional[str] = Field(None, description="Clinical usage context")
    examples: List[str] = Field(default_factory=list, description="Example values")
    common_issues: List[str] = Field(default_factory=list, description="Common data quality issues")


class PlainLanguageOutput(BaseAgentOutput):
    """Output from PlainLanguageAgent."""

    documentation: List[FieldDocumentation] = Field(default_factory=list, description="Field documentation")


# ============================================================================
# Validation Agent Output
# ============================================================================

class ValidationIssue(BaseModel):
    """Individual validation issue."""

    severity: Literal["error", "warning", "info"] = Field(..., description="Issue severity")
    category: str = Field(..., description="Issue category")
    message: str = Field(..., description="Issue description")
    field: Optional[str] = Field(None, description="Affected field (if applicable)")
    suggestion: Optional[str] = Field(None, description="Suggested fix")


class ValidationOutput(BaseAgentOutput):
    """Output from ValidationAgent."""

    validation_passed: bool = Field(..., description="Overall validation result")
    overall_score: float = Field(..., ge=0.0, le=1.0, description="Quality score")
    issues_found: List[ValidationIssue] = Field(default_factory=list, description="Validation issues")
    recommendations: List[str] = Field(default_factory=list, description="Improvement recommendations")


# ============================================================================
# Design Improvement Output
# ============================================================================

class DesignMetrics(BaseModel):
    """Design quality metrics."""

    clarity_score: float = Field(..., ge=0.0, le=1.0)
    completeness_score: float = Field(..., ge=0.0, le=1.0)
    consistency_score: float = Field(..., ge=0.0, le=1.0)
    overall_score: float = Field(..., ge=0.0, le=1.0)


class DesignImprovementOutput(BaseAgentOutput):
    """Output from DesignImprovementAgent."""

    improved_content: str = Field(..., description="Improved documentation")
    metrics_before: DesignMetrics = Field(..., description="Metrics before improvement")
    metrics_after: DesignMetrics = Field(..., description="Metrics after improvement")
    improvements_made: List[str] = Field(default_factory=list, description="List of improvements")


# ============================================================================
# Higher Level Documentation Output
# ============================================================================

class InstrumentDocumentation(BaseModel):
    """Higher-level instrument documentation."""

    instrument_name: str = Field(..., description="Instrument/form name")
    description: str = Field(..., description="Overall description")
    num_variables: int = Field(..., ge=0, description="Number of variables")
    variable_list: List[str] = Field(default_factory=list, description="List of variable names")
    markdown_documentation: str = Field(..., description="Complete markdown documentation")
    sections: List[str] = Field(default_factory=list, description="Section names")


class HigherLevelDocOutput(BaseAgentOutput):
    """Output from HigherLevelDocumentationAgent."""

    instruments: List[InstrumentDocumentation] = Field(default_factory=list, description="Instrument docs")


# ============================================================================
# Review Queue Item
# ============================================================================

class ReviewQueueItem(BaseModel):
    """Structured review queue item."""

    item_id: str = Field(..., description="Unique item ID")
    job_id: str = Field(..., description="Associated job ID")
    agent_name: str = Field(..., description="Agent that created this item")
    item_type: str = Field(..., description="Type of item being reviewed")
    content: str = Field(..., description="Content to review")
    status: ReviewStatus = Field(default=ReviewStatus.PENDING, description="Review status")
    reviewer_notes: Optional[str] = Field(None, description="Notes from reviewer")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Agent's confidence")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    reviewed_at: Optional[datetime] = Field(None, description="Review timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


# ============================================================================
# Job Tracking
# ============================================================================

class Job(BaseModel):
    """Processing job."""

    job_id: str = Field(..., description="Unique job ID")
    source_file: str = Field(..., description="Source file name")
    status: JobStatus = Field(default=JobStatus.RUNNING, description="Job status")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Job metadata")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    error_message: Optional[str] = Field(None, description="Error message if failed")


# ============================================================================
# Utility Functions
# ============================================================================

def parse_agent_output(
    response_text: str,
    output_class: type[BaseAgentOutput],
    fallback_to_dict: bool = True
) -> BaseAgentOutput:
    """
    Parse LLM response into structured Pydantic model.

    Args:
        response_text: Raw LLM response
        output_class: Pydantic model class to parse into
        fallback_to_dict: If True, return basic output on parse failure

    Returns:
        Parsed Pydantic model instance

    Raises:
        ValueError: If parsing fails and fallback_to_dict=False
    """
    from core_fixes import safe_parse_json

    try:
        # Try to parse JSON from response
        data = safe_parse_json(response_text, strict=False)

        if data:
            return output_class(**data)

    except Exception as e:
        if not fallback_to_dict:
            raise ValueError(f"Failed to parse {output_class.__name__}: {e}")

    # Fallback: create minimal valid output
    return output_class(
        content=response_text,
        confidence=0.0,
        needs_human_review=True,
        warnings=["Failed to parse structured output, falling back to raw text"]
    )

