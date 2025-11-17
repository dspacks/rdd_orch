# ADE Agent Documentation

Complete reference for all agents in the Agent Development Environment (ADE) system.

---

## Agent Architecture Overview

```
┌─────────────────────────────────────┐
│           BaseAgent                  │
│  • API Configuration                 │
│  • Toon Injection                    │
│  • Toon Notation Encoding            │
│  • Prompt Building                   │
└─────────────┬───────────────────────┘
              │
    ┌─────────┴─────────┐
    │                   │
┌───▼───┐         ┌─────▼─────┐
│ Core  │         │ Extended  │
│Agents │         │  Agents   │
└───────┘         └───────────┘
```

All agents inherit from `BaseAgent`, which provides:
- Gemini API integration
- Toon notation encoding for 40-70% token reduction
- Context injection via Toons
- Rate limiting and configuration management

---

## Core Agents (Primary Pipeline)

### 1. DataParserAgent

**Purpose:** Converts raw data dictionaries into standardized JSON format.

**Input:** Raw CSV, XML, or text data
**Output:** Structured JSON

```python
class DataParserAgent(BaseAgent):
    """
    First agent in the pipeline. Parses various input formats
    into a standardized JSON structure for downstream agents.
    """
```

**Usage:**
```python
parser = DataParserAgent()
parsed_data = parser.process(raw_csv_string)
# Returns: JSON with standardized field structure
```

**Expected Output Format:**
```json
{
  "fields": [
    {
      "name": "patient_id",
      "type": "text",
      "label": "Patient ID",
      "choices": null,
      "notes": "Unique identifier"
    }
  ]
}
```

---

### 2. TechnicalAnalyzerAgent

**Purpose:** Infers technical properties and mappings for each field.

**Input:** Parsed JSON from DataParserAgent
**Output:** Technical analysis with inferred properties

```python
class TechnicalAnalyzerAgent(BaseAgent):
    """
    Analyzes field metadata to infer data types, cardinality,
    valid ranges, and technical constraints.
    Uses Toon notation internally for efficiency.
    """
```

**Usage:**
```python
analyzer = TechnicalAnalyzerAgent()
analyzer.inject_toons(relevant_toons)
technical_info = analyzer.process(parsed_data)
```

**Output Includes:**
- Inferred data type (continuous, categorical, ordinal)
- Cardinality (required, optional)
- Valid value ranges
- Format constraints
- Potential issues flagged

---

### 3. DomainOntologyAgent

**Purpose:** Maps fields to standard healthcare ontologies.

**Input:** Technical analysis from TechnicalAnalyzerAgent
**Output:** Ontology mappings (OMOP, LOINC, SNOMED, RxNorm, HGNC)

```python
class DomainOntologyAgent(BaseAgent):
    """
    Maps healthcare data fields to standard ontologies.
    Leverages domain knowledge and Toon instructions for
    consistent, accurate mappings.
    """
```

**Usage:**
```python
ontology_agent = DomainOntologyAgent()
ontology_agent.inject_toons(mapping_toons)
mappings = ontology_agent.process(technical_info)
```

**Supported Ontologies:**
- **OMOP CDM** - Observational Medical Outcomes Partnership
- **LOINC** - Logical Observation Identifiers Names and Codes
- **SNOMED CT** - Systematized Nomenclature of Medicine
- **RxNorm** - Normalized names for clinical drugs
- **HGNC** - HUGO Gene Nomenclature Committee

---

### 4. PlainLanguageAgent

**Purpose:** Generates human-readable documentation for each field.

**Input:** Technical analysis and ontology mappings
**Output:** Plain language documentation in Markdown

```python
class PlainLanguageAgent(BaseAgent):
    """
    Transforms technical specifications into clear,
    understandable documentation for diverse audiences.
    """
```

**Usage:**
```python
plain_agent = PlainLanguageAgent()
documentation = plain_agent.process(combined_data)
```

**Output Includes:**
- Clear field descriptions
- Clinical context
- Data collection guidance
- Common use cases
- Important notes for users

---

### 5. DocumentationAssemblerAgent

**Purpose:** Compiles all agent outputs into final documentation.

**Input:** All approved content from review queue
**Output:** Complete Markdown documentation

```python
class DocumentationAssemblerAgent(BaseAgent):
    """
    Final assembly agent that creates cohesive, well-structured
    documentation from individual field documentation.
    """
```

**Usage:**
```python
assembler = DocumentationAssemblerAgent()
final_doc = assembler.process(approved_items)
```

---

## Extended Agents (Quality & Enhancement)

### 6. ValidationAgent

**Purpose:** Validates outputs from other agents for quality and consistency.

**Input:** Agent outputs (any type)
**Output:** Validation report with scores and recommendations

```python
class ValidationAgent(BaseAgent):
    """
    Quality assurance agent that reviews and validates
    all agent outputs for correctness, completeness,
    and consistency.
    """
```

**Tasks:**
1. Review outputs for correctness and completeness
2. Check consistency across different agent outputs
3. Identify errors, inconsistencies, or missing information
4. Validate data types, formats, and standards compliance
5. Ensure ontology mappings are accurate
6. Verify documentation clarity and completeness

**Usage:**
```python
validator = ValidationAgent()
result = validator.process(agent_output)

# Example output:
{
  "validation_passed": true,
  "overall_score": 85,
  "issues_found": [
    {
      "type": "warning",
      "description": "Missing SNOMED mapping",
      "field": "bp_systolic"
    }
  ],
  "recommendations": [
    "Consider adding RxNorm mapping for medication fields"
  ]
}
```

---

### 7. VersionControlAgent

**Purpose:** Tracks documentation versions and manages change history.

**Input:** Documentation elements and changes
**Output:** Version information and history

```python
class VersionControlAgent(BaseAgent):
    """
    Manages documentation versioning, tracking changes
    over time with author attribution and timestamps.
    """

    def __init__(self, db_manager: DatabaseManager, config: APIConfig = None):
        # Requires database connection for persistence
```

**Methods:**
```python
# Create a new version
version_info = version_agent.create_version(
    element_id="bp_systolic",
    element_type="field",
    content="Updated documentation...",
    author="reviewer_name"
)

# Get version history
history = version_agent.get_history(element_id, element_type)

# Compare versions
diff = version_agent.compare_versions(version_1, version_2)
```

---

### 8. DataConventionsAgent

**Purpose:** Analyzes and enforces data naming conventions.

**Input:** Parsed data or variable names
**Output:** Convention compliance report

```python
class DataConventionsAgent(BaseAgent):
    """
    Ensures consistent naming patterns across the data dictionary.
    Identifies violations and suggests standardized names.
    """
```

**Tasks:**
1. Analyze variable naming patterns
2. Check compliance with standards (snake_case, camelCase, etc.)
3. Identify convention violations and warnings
4. Suggest standardized names

**Usage:**
```python
conventions_agent = DataConventionsAgent()
report = conventions_agent.process(parsed_data)

# Example output:
{
  "naming_pattern": "snake_case",
  "convention_compliance": 85,
  "convention_warnings": [
    "Variable 'PatientID' uses PascalCase instead of snake_case",
    "Variable 'bp_sys' uses abbreviation"
  ],
  "suggested_name": "patient_id"
}
```

---

### 9. DesignImprovementAgent

**Purpose:** Enhances documentation design, clarity, and structure.

**Input:** Draft documentation
**Output:** Improved documentation with scores

```python
class DesignImprovementAgent(BaseAgent):
    """
    Improves the quality of documentation by enhancing
    structure, clarity, and completeness. Provides
    before/after scoring.
    """
```

**Tasks:**
1. Review provided documentation
2. Identify areas for improvement in structure, clarity, and completeness
3. Suggest and apply design enhancements
4. Score the design before and after improvements

**Usage:**
```python
design_agent = DesignImprovementAgent()
result = design_agent.process(draft_documentation)

# Example output:
{
  "improved_content": "Enhanced documentation text...",
  "design_score": {
    "before": 70,
    "after": 85
  },
  "improvements_made": [
    "Added structured sections",
    "Improved clinical context",
    "Enhanced readability"
  ]
}
```

---

### 10. HigherLevelDocumentationAgent

**Purpose:** Generates documentation for instruments, segments, and codebooks.

**Input:** Groups of related variables
**Output:** Higher-level documentation structures

```python
class HigherLevelDocumentationAgent(BaseAgent):
    """
    Creates documentation at the instrument and segment level,
    grouping related variables into logical units.
    """
```

**Tasks:**
1. Group related variables into logical instruments/segments
2. Generate comprehensive documentation for groupings
3. Create codebook overviews

**Usage:**
```python
higher_level_agent = HigherLevelDocumentationAgent()
instrument_doc = higher_level_agent.process(variables_group)

# Example output:
{
  "instrument_name": "Vital Signs Assessment",
  "description": "Standard vital signs measurements...",
  "variables": ["bp_systolic", "bp_diastolic", "heart_rate", "temperature"],
  "documentation_markdown": "## Vital Signs Assessment\n\n..."
}
```

---

## Testing Agents

### ValidationAgentTester

**Purpose:** Test harness for ValidationAgent performance.

```python
class ValidationAgentTester:
    """
    Comprehensive testing framework for validation agent
    performance and accuracy.
    """
```

**Provides:**
- Automated test cases for validation
- Performance metrics
- Edge case testing
- Consistency checks

---

## Agent Configuration

### APIConfig

Configure rate limiting and API behavior:

```python
@dataclass
class APIConfig:
    tier: str = "free"  # "free" or "paid"
    requests_per_minute: int = 15
    requests_per_day: int = 1500
    retry_attempts: int = 3
    retry_delay: float = 1.0
```

### Using Toons with Agents

All agents support Toon injection for enhanced context:

```python
# Create relevant toons
toon_manager = ToonManager(db)
mapping_toon = toon_manager.create_toon(
    name="BP_Mapping_Rules",
    toon_type=ToonType.INSTRUCTION,
    content="Blood pressure mapping guidelines..."
)

# Inject into agents
agent.inject_toons([mapping_toon])

# Agent now uses this context in all requests
result = agent.process(data)
```

---

## Agent Pipeline Flow

```
Raw Data → [DataParser] → Parsed JSON
                              ↓
                    [TechnicalAnalyzer] → Technical Properties
                              ↓
                    [DomainOntology] → Ontology Mappings
                              ↓
                    [PlainLanguage] → Human Documentation
                              ↓
                    [DocumentationAssembler] → Final Output
                              ↓
                    [ValidationAgent] → Quality Check (Optional)
                              ↓
                    [DesignImprovement] → Enhanced Output (Optional)
```

---

## Best Practices

### 1. Always Inject Relevant Toons
```python
# Create domain-specific instructions
toon_manager.create_toon(
    name="Project_Guidelines",
    toon_type=ToonType.INSTRUCTION,
    content="Specific guidelines for this project..."
)

# Inject before processing
agent.inject_toons(toon_manager.list_toons())
```

### 2. Validate Critical Outputs
```python
# Always validate ontology mappings
validator = ValidationAgent()
validation = validator.process(ontology_output)

if not validation['validation_passed']:
    # Review issues before proceeding
    for issue in validation['issues_found']:
        print(f"Issue: {issue['description']}")
```

### 3. Track Important Changes
```python
# Use version control for significant updates
version_agent = VersionControlAgent(db)
version_agent.create_version(
    element_id=field_id,
    element_type="field",
    content=updated_doc,
    author="reviewer"
)
```

### 4. Monitor API Usage
```python
# Use appropriate configuration
config = APIConfig(tier="free", requests_per_minute=15)
agent = ValidationAgent(config=config)
```

---

## Error Handling

All agents handle errors gracefully:

```python
try:
    result = agent.process(data)
except APIError as e:
    # API quota exceeded or rate limited
    print(f"API Error: {e}")
    # Consider retry logic
except ValidationError as e:
    # Input validation failed
    print(f"Invalid input: {e}")
except Exception as e:
    # General error
    print(f"Processing error: {e}")
```

---

## See Also

- [README.md](README.md) - Project overview
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Common code snippets
- [ADVANCED_FEATURES.md](ADVANCED_FEATURES.md) - Batch processing and validation details
- [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) - Database table documentation

---

**Last Updated:** 2025-11-17
