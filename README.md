# Agent Development Environment (ADE) for Healthcare Data Documentation

![Version](https://img.shields.io/badge/version-3.1-blue)
![License](https://img.shields.io/badge/license-MIT-green)

A specialized development environment for building, testing, and managing AI agents using the Google Gemini API. The ADE creates an orchestrator and team of sub-agents that transform complex healthcare data specifications into comprehensive, human-readable documentation.

## Overview

The ADE system ingests technical data specifications (CSV, XML, JSON) that are often imperfect or incomplete, and produces comprehensive documentation through a Human-in-the-Loop (HITL) workflow. The final output serves as a "source of truth" for interdisciplinary teams to understand data relationships, constraints, design rationale, and version history.

## Key Features

### 🤖 **Multi-Agent System**

**Core Agents:**
- **DataParserAgent** - Converts raw data to standardized JSON
- **TechnicalAnalyzerAgent** - Infers field mappings and properties (uses Toon notation for 40-70% token reduction)
- **DomainOntologyAgent** - Maps to standard healthcare ontologies (OMOP, LOINC, SNOMED) with Toon encoding
- **PlainLanguageAgent** - Generates human-readable documentation using Toon notation for efficiency
- **DocumentationAssemblerAgent** - Compiles final documentation

**Extended Agents (NEW):**
- **ValidationAgent** - Validates outputs for quality and consistency, checks ontology mapping accuracy
- **VersionControlAgent** - Tracks documentation versions and manages change history
- **DataConventionsAgent** - Analyzes naming patterns and enforces data conventions (snake_case, camelCase, etc.)
- **DesignImprovementAgent** - Enhances documentation design, clarity, and structure with scoring
- **HigherLevelDocumentationAgent** - Generates instrument-level, segment, and codebook documentation

**💡 All agents now use Toon notation internally** to reduce API token usage by 40-70% per agent call.

### 📚 **Toon System - Context Management**
A unique system for managing large files and agent context:
- **Toon_Summary** - High-level summaries of large documents
- **Toon_Chunk** - Specific logical pieces of documents
- **Toon_Instruction** - Reusable instructions
- **Toon_Version** - Change descriptions
- **Toon_Design** - Design decision rationale
- **Toon_Mapping** - Saved mappings for automation

### 🔄 **Human-in-the-Loop Workflow**
- Review and approve agent-generated content
- Request clarifications for ambiguous data
- Edit and refine documentation
- Track approval status

### 💾 **SQLite Persistence**
- Project-local database for all data
- Complete audit trail
- Session history and context management
- Working vs long-term memory separation

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface                            │
│  (Jupyter Notebook / Kaggle)                                │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                  Orchestrator                                │
│  (Workflow Management & Agent Coordination)                  │
└─┬──────┬──────┬──────┬──────┬──────────────────────────────┘
  │      │      │      │      │
  ▼      ▼      ▼      ▼      ▼
┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐
│DP  │→│TA  │→│DO  │→│PL  │→│DA  │  (Core Agents)
└────┘ └────┘ └────┘ └────┘ └────┘
  │      │      │      │      │
  └──────┴──────┴──────┴──────┘
             │
        ┌────▼────┐
        │Extended │
        │ Agents  │
        └─────────┘
    ┌────┬────┬────┬────┐
    │VA  │VC  │DC  │DI  │ HL (Extended)
    └────┴────┴────┴────┘
             │
┌────────────▼────────────────────────────────────────────────┐
│                  SQLite Database                             │
│  • Toons (Context Library)                                   │
│  • ReviewQueue (HITL Workflow)                              │
│  • Jobs (Tracking)                                          │
│  • SessionHistory (Memory)                                  │
│  • SystemState (Persistence)                                │
└──────────────────────────────────────────────────────────────┘

Legend: DP=DataParser, TA=TechnicalAnalyzer, DO=DomainOntology,
        PL=PlainLanguage, DA=DocumentationAssembler
        VA=Validation, VC=VersionControl, DC=DataConventions,
        DI=DesignImprovement, HL=HigherLevelDocumentation
```

## Quick Start

### Prerequisites

1. **Kaggle Account** (or local Jupyter environment)
2. **Google Gemini API Key** - Get one at [Google AI Studio](https://makersuite.google.com/app/apikey)

### Setup in Kaggle

1. **Upload the Notebook**
   - Go to Kaggle and create a new notebook
   - Upload `ade_healthcare_documentation.ipynb`

2. **Add API Key**
   - Go to notebook Settings → Secrets
   - Add a new secret named `GOOGLE_API_KEY`
   - Paste your Gemini API key

3. **Run the Notebook**
   - Execute cells in order
   - The first run will initialize the database and create sample data

### Local Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/rdd_orch.git
cd rdd_orch

# Install dependencies
pip install -q google-generativeai pandas numpy jupyter

# Set your API key
export GOOGLE_API_KEY="your-api-key-here"

# Launch Jupyter
jupyter notebook ade_healthcare_documentation.ipynb
```

## Usage Examples

### Basic Workflow

```python
# Initialize the system
db = DatabaseManager("project.db")
db.connect()
db.initialize_schema()

orchestrator = Orchestrator(db)

# Process a data dictionary
job_id = orchestrator.process_data_dictionary(
    source_data=your_data_dictionary,
    source_file="my_study.csv",
    auto_approve=False  # Enable manual review
)

# Review pending items
pending = orchestrator.review_queue.get_pending_items(job_id)
for item in pending:
    # Review and approve/reject
    orchestrator.review_queue.approve_item(item.item_id)

# Generate final documentation
documentation = orchestrator.finalize_documentation(job_id)
```

### Working with Toons

```python
# Create a Toon for reusable instructions
toon_manager = ToonManager(db)

toon_id = toon_manager.create_toon(
    name="OMOP_Mapping_Guidelines",
    toon_type=ToonType.INSTRUCTION,
    content="Always map blood pressure to OMOP concept 3004249..."
)

# Inject Toons into agent context
toons = toon_manager.list_toons()
orchestrator.domain_ontology.inject_toons(toons)
```

### Managing Context

```python
# Monitor working memory
context_manager = ContextManager(db)
memory = context_manager.get_working_memory(job_id)

print(f"Tokens: {memory['total_tokens']}")
print(f"Needs compaction: {memory['needs_compaction']}")

# Compact if needed
if memory['needs_compaction']:
    summary = context_manager.compact_context(job_id)
```

### Using Extended Agents

```python
# Validate agent outputs for quality
validator = ValidationAgent()
validation_result = validator.process(agent_output)
# Returns: validation_passed, overall_score, issues_found, recommendations

# Check data naming conventions
conventions_agent = DataConventionsAgent()
conventions_report = conventions_agent.process(parsed_data)
# Returns: naming_pattern, convention_compliance score, warnings, suggestions

# Improve documentation design
design_agent = DesignImprovementAgent()
improved_doc = design_agent.process(documentation)
# Returns: improved_content, design_score (before/after), improvements_made

# Track documentation versions
version_agent = VersionControlAgent(db)
version_info = version_agent.create_version(
    element_id="bp_systolic",
    element_type="field",
    content=new_documentation,
    author="reviewer"
)

# Generate higher-level documentation
higher_level_agent = HigherLevelDocumentationAgent()
instrument_doc = higher_level_agent.process(variables_group)
# Returns: instrument_name, description, variables list, markdown documentation
```

## Database Schema

### Core Tables

**Agents**
- Stores agent definitions and system prompts

**Toons**
- Context snippets library
- 6 different types for various use cases

**Jobs**
- Tracks processing jobs
- Links to source files and status

**ReviewQueue**
- Central HITL workflow management
- Statuses: Pending, Approved, Rejected, Needs_Clarification

**SessionHistory**
- Chat logs and conversation history
- Supports context compaction

**SystemState**
- Application state persistence
- Resume sessions functionality

## Advanced Features

### Toon Notation System

**Compact data encoding** that reduces token usage by 40-70%:

```python
# JSON (verbose)
{"items": [{"id": 1, "qty": 5}, {"id": 2, "qty": 3}]}

# Toon notation (compact)
items[2]{id,qty}:
  1,5
  2,3
```

**Key features:**
- Tabular format for uniform arrays
- Inline notation for primitive arrays
- Smart quoting for ambiguous values
- Preserves all information
- **40-70% token savings** on data-heavy prompts

### Context Compaction

When session history grows large:
1. Automatic triggering at 80% of context limit
2. ContextCompactorAgent summarizes conversation
3. Summary stored as Toon_Summary
4. Full history preserved in database

### Clarification Workflow

For ambiguous data:
1. Agent flags field with `needs_clarification: true`
2. Item added to ReviewQueue with status `Needs_Clarification`
3. Human provides clarification response
4. Orchestrator re-processes with clarification context

### Ontology Mapping

Supports standard healthcare terminologies:
- **OMOP CDM** - Common Data Model concepts
- **LOINC** - Lab and clinical observations
- **SNOMED CT** - Clinical terminology
- **RxNorm** - Medications
- **HGNC** - Gene nomenclature

## Example Data Dictionary Format

The system accepts various formats. Here's a REDCap-style example:

```csv
Variable Name,Field Type,Field Label,Choices,Notes
patient_id,text,Patient ID,,Unique identifier
age,integer,Age (years),,Age at enrollment
sex,radio,Biological Sex,"1, Male | 2, Female",
bp_systolic,integer,Systolic BP (mmHg),,
diagnosis_date,date,Diagnosis Date,,Date of primary diagnosis
```

## Output Example

The system generates comprehensive Markdown documentation:

```markdown
## Variable: bp_systolic

**Description:** Systolic blood pressure measurement in millimeters of mercury (mmHg)

**Technical Details:**
- Data Type: continuous
- Cardinality: required
- Valid Values: 70-250 mmHg

**Standard Ontology Mappings:**
- OMOP: 3004249 - Systolic blood pressure
- LOINC: 8480-6 - Systolic blood pressure

**Clinical Context:** Essential vital sign for cardiovascular assessment...
```

## System Requirements

- Python 3.8+
- Google Gemini API access
- SQLite3 (included with Python)
- 2GB RAM minimum
- Internet connection for API calls

## Configuration

### Gemini Model Selection

Default: `gemini-2.0-flash-exp`

To change:
```python
agent = BaseAgent(
    name="CustomAgent",
    system_prompt="...",
    model_name="gemini-1.5-pro"  # or other model
)
```

### Context Window Settings

```python
context_manager = ContextManager(
    db_manager=db,
    max_tokens=100000,  # Adjust based on model
)
```

## Troubleshooting

### API Key Issues
```
Error: API key not valid
```
- Verify key in Kaggle Secrets
- Check key has Gemini API enabled
- Ensure no extra whitespace

### Database Locked
```
Error: database is locked
```
- Close other connections
- Restart the kernel
- Check file permissions

### Memory Issues
```
Context too large
```
- Run context compaction
- Clear working memory
- Reduce active Toons

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Citation

If you use this system in your research, please cite:

```bibtex
@software{ade_healthcare_2024,
  title={Agent Development Environment for Healthcare Data Documentation},
  author={Your Name},
  year={2024},
  version={3.0},
  url={https://github.com/yourusername/rdd_orch}
}
```

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/rdd_orch/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/rdd_orch/discussions)
- **Documentation**: See notebook comments and docstrings

## Roadmap

### Version 3.1 (Current - Completed)
- [x] Extended agent system (Validation, VersionControl, DataConventions, DesignImprovement, HigherLevelDocumentation)
- [x] Batch processing for multiple files (SnippetManager, BatchProcessor)
- [x] Version control for documentation (VersionControlAgent)
- [x] Validation testing framework (ValidationAgent, ValidationAgentTester)
- [ ] Web UI using Streamlit
- [ ] Export to multiple formats (PDF, HTML)
- [ ] Integration with REDCap API

### Version 4.0 (Future)
- [ ] Multi-user support
- [ ] Custom agent templates
- [ ] Plugin system for ontologies
- [ ] Advanced analytics and reporting dashboard

## Acknowledgments

Built with:
- Google Gemini API
- SQLite
- Pandas
- Python ecosystem

Inspired by the need for better healthcare data documentation and the power of AI-assisted workflows.

---

**Status**: Active Development
**Last Updated**: 2025-11-17
**Maintainer**: dspacks
