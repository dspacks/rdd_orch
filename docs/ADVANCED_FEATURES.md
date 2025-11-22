# ADE Advanced Features

This document covers advanced features including batch processing, validation testing, version control, and API configuration.

---

## Table of Contents

1. [Batch Processing](#batch-processing)
2. [Validation Testing Framework](#validation-testing-framework)
3. [Version Control System](#version-control-system)
4. [API Rate Limiting & Configuration](#api-rate-limiting--configuration)
5. [Data Convention Enforcement](#data-convention-enforcement)
6. [Design Improvement Workflows](#design-improvement-workflows)
7. [Higher-Level Documentation Generation](#higher-level-documentation-generation)

---

## Batch Processing

### Overview

The ADE system includes `SnippetManager` and `BatchProcessor` classes for efficiently processing multiple data dictionaries or large datasets.

### SnippetManager

Manages chunks of data for large file processing:

```python
class SnippetManager:
    """
    Manages snippets/chunks of data for efficient processing.
    Useful when dealing with large data dictionaries that exceed
    context windows or API limits.
    """
```

**Usage:**
```python
snippet_manager = SnippetManager(db_manager)

# Create snippets from large dataset
snippets = snippet_manager.create_snippets(
    data=large_data_dictionary,
    chunk_size=50  # Number of fields per snippet
)

# Process each snippet
for snippet_id in snippets:
    snippet_data = snippet_manager.get_snippet(snippet_id)
    result = orchestrator.process_data_dictionary(
        source_data=snippet_data,
        source_file=f"chunk_{snippet_id}.csv"
    )

# Reassemble results
final_results = snippet_manager.reassemble_results(snippets)
```

### BatchProcessor

Processes multiple files or datasets in batch:

```python
class BatchProcessor:
    """
    Handles batch processing of multiple data dictionaries
    with progress tracking and error handling.
    """
```

**Usage:**
```python
batch_processor = BatchProcessor(orchestrator)

# Define batch of files
files_to_process = [
    "study_a.csv",
    "study_b.csv",
    "study_c.csv"
]

# Process batch with progress tracking
results = batch_processor.process_batch(
    files=files_to_process,
    auto_approve=False,
    on_progress=lambda f, pct: print(f"{f}: {pct}% complete")
)

# Results contain job_ids for each file
for file_name, job_id in results.items():
    print(f"{file_name} -> Job ID: {job_id}")
```

### Batch Processing Best Practices

1. **Monitor API usage** - Batch processing can quickly hit rate limits
2. **Handle failures gracefully** - Some files may fail while others succeed
3. **Review systematically** - Use batch review workflows for efficiency
4. **Track progress** - Log job IDs and status for auditing

```python
# Example: Robust batch processing with error handling
def safe_batch_process(files, orchestrator):
    results = {}
    errors = {}

    for file_path in files:
        try:
            with open(file_path, 'r') as f:
                data = f.read()

            job_id = orchestrator.process_data_dictionary(
                source_data=data,
                source_file=file_path,
                auto_approve=False
            )
            results[file_path] = job_id

        except Exception as e:
            errors[file_path] = str(e)
            continue

    return results, errors

results, errors = safe_batch_process(files, orchestrator)

if errors:
    print("Failed files:")
    for file, error in errors.items():
        print(f"  {file}: {error}")
```

---

## Validation Testing Framework

### ValidationAgent

Quality assurance for all agent outputs:

```python
validator = ValidationAgent()
```

**Validation Checks:**
1. **Correctness** - Output matches expected format and content
2. **Completeness** - All required fields present
3. **Consistency** - No contradictions across outputs
4. **Standards Compliance** - Follows healthcare data standards
5. **Ontology Accuracy** - Mappings are appropriate and valid
6. **Documentation Quality** - Clear, accurate, and complete

**Example Validation Workflow:**
```python
# After each agent in pipeline
parser_output = parser_agent.process(raw_data)
parser_validation = validator.process(parser_output)

if not parser_validation['validation_passed']:
    print("Parser output validation failed!")
    for issue in parser_validation['issues_found']:
        print(f"  - {issue['type']}: {issue['description']}")
    # Handle the failure
else:
    print(f"Parser validation score: {parser_validation['overall_score']}")
    # Continue to next agent
```

### ValidationAgentTester

Systematic testing of validation capabilities:

```python
class ValidationAgentTester:
    """
    Test harness for ensuring validation agent performs correctly
    across various scenarios.
    """
```

**Testing Methods:**

```python
tester = ValidationAgentTester()

# Test with known good data
tester.test_valid_output()

# Test with known bad data
tester.test_invalid_output()

# Test edge cases
tester.test_edge_cases()

# Test consistency across runs
tester.test_consistency()

# Performance benchmarking
metrics = tester.benchmark_performance()
print(f"Average processing time: {metrics['avg_time']}ms")
print(f"Accuracy rate: {metrics['accuracy']}%")
```

**Example Edge Cases:**
- Empty outputs
- Malformed JSON
- Missing ontology mappings
- Contradictory information
- Unusual field types
- Non-standard naming conventions

---

## Version Control System

### VersionControlAgent

Track documentation changes over time:

```python
version_agent = VersionControlAgent(db_manager)
```

**Creating Versions:**
```python
# Create initial version
version_info = version_agent.create_version(
    element_id="patient_id",
    element_type="field",
    content="Initial documentation for patient_id...",
    author="system"
)

print(f"Created version: {version_info['version']}")
print(f"Timestamp: {version_info['created_at']}")

# Update with new version
updated_version = version_agent.create_version(
    element_id="patient_id",
    element_type="field",
    content="Updated documentation with additional context...",
    author="reviewer_john"
)

# Version automatically incremented
print(f"New version: {updated_version['version']}")
```

**Retrieving History:**
```python
# Get all versions for an element
history = version_agent.get_history(
    element_id="patient_id",
    element_type="field"
)

for version_entry in history:
    print(f"Version {version_entry['version']}:")
    print(f"  Author: {version_entry['author']}")
    print(f"  Date: {version_entry['created_at']}")
    print(f"  Content preview: {version_entry['content'][:100]}...")
```

**Comparing Versions:**
```python
# Compare two specific versions
diff = version_agent.compare_versions(
    element_id="patient_id",
    version_a="1.0",
    version_b="2.0"
)

print("Changes between versions:")
for change in diff['changes']:
    print(f"  {change}")
```

**Version Control Best Practices:**
1. Always attribute changes to authors
2. Create versions before major updates
3. Maintain audit trail for compliance
4. Use meaningful version descriptions

---

## API Rate Limiting & Configuration

### APIConfig

Configure API behavior to prevent rate limit errors:

```python
@dataclass
class APIConfig:
    tier: str = "free"           # "free" or "paid"
    requests_per_minute: int = 15
    requests_per_day: int = 1500
    retry_attempts: int = 3
    retry_delay: float = 1.0
```

### Tier-Based Configuration

**Free Tier (Default):**
```python
free_config = APIConfig(
    tier="free",
    requests_per_minute=15,
    requests_per_day=1500,
    retry_attempts=3,
    retry_delay=2.0  # Longer delays for free tier
)

agent = ValidationAgent(config=free_config)
```

**Paid Tier:**
```python
paid_config = APIConfig(
    tier="paid",
    requests_per_minute=60,
    requests_per_day=10000,
    retry_attempts=5,
    retry_delay=0.5
)

agent = ValidationAgent(config=paid_config)
```

### Automatic Rate Limiting

Agents automatically manage rate limits:

```python
# Agent tracks and respects limits
for i in range(20):
    result = agent.process(data)
    # Automatic delays applied if approaching limits
```

### Monitoring Usage

```python
# Check current API usage
usage = agent.get_usage_stats()
print(f"Requests this minute: {usage['minute_count']}")
print(f"Requests today: {usage['daily_count']}")
print(f"Remaining today: {usage['daily_remaining']}")
```

### Cost Optimization

**Strategies:**
1. **Use Toon notation** - 40-70% token reduction
2. **Batch similar requests** - Process related fields together
3. **Cache results** - Avoid re-processing identical inputs
4. **Prioritize validation** - Only validate critical outputs

```python
# Example: Efficient batch processing with rate awareness
def rate_aware_processing(items, agent, config):
    results = []

    for i, item in enumerate(items):
        # Check if approaching limit
        if agent.approaching_rate_limit():
            print(f"Approaching rate limit, pausing...")
            time.sleep(60)  # Wait for limit reset

        result = agent.process(item)
        results.append(result)

        # Progress update
        if i % 10 == 0:
            print(f"Processed {i}/{len(items)}")

    return results
```

---

## Data Convention Enforcement

### DataConventionsAgent

Ensure consistent naming patterns:

```python
conventions_agent = DataConventionsAgent()
```

**Analyzing Conventions:**
```python
# Analyze a single variable
result = conventions_agent.analyze_variable("PatientID")

# Output:
{
  "original_name": "PatientID",
  "naming_pattern": "PascalCase",
  "convention_compliance": 60,
  "convention_warnings": [
    "Uses PascalCase instead of recommended snake_case",
    "Consider lowercase for better compatibility"
  ],
  "suggested_name": "patient_id"
}
```

**Batch Convention Check:**
```python
# Analyze entire data dictionary
variables = ["PatientID", "bp_systolic", "AgeYears", "sex", "DiagnosisDate"]

compliance_report = conventions_agent.analyze_batch(variables)

print(f"Overall compliance: {compliance_report['overall_score']}%")
print(f"Detected pattern: {compliance_report['dominant_pattern']}")
print("\nRecommendations:")
for rec in compliance_report['recommendations']:
    print(f"  - {rec}")
```

**Enforcing Standards:**
```python
# Apply consistent naming
standardized = conventions_agent.standardize_names(
    variables=original_names,
    target_convention="snake_case"
)

# Generate renaming script
rename_script = conventions_agent.generate_rename_script(standardized)
```

---

## Design Improvement Workflows

### DesignImprovementAgent

Enhance documentation quality:

```python
design_agent = DesignImprovementAgent()
```

**Improving Draft Documentation:**
```python
draft_doc = """
## bp_systolic
Blood pressure systolic measurement.
Type: integer
"""

improved = design_agent.process(draft_doc)

print("Original Score:", improved['design_score']['before'])
print("Improved Score:", improved['design_score']['after'])
print("\nImprovements Made:")
for improvement in improved['improvements_made']:
    print(f"  - {improvement}")

print("\n--- Improved Content ---")
print(improved['improved_content'])
```

**Iterative Improvement:**
```python
# Multiple passes for best results
doc = initial_draft
max_passes = 3
target_score = 90

for i in range(max_passes):
    result = design_agent.process(doc)

    if result['design_score']['after'] >= target_score:
        print(f"Target score reached after {i+1} passes")
        break

    doc = result['improved_content']
    print(f"Pass {i+1}: Score {result['design_score']['after']}")

final_doc = doc
```

---

## Higher-Level Documentation Generation

### HigherLevelDocumentationAgent

Create instrument and codebook documentation:

```python
higher_level_agent = HigherLevelDocumentationAgent()
```

**Grouping Variables into Instruments:**
```python
# Group related vital signs
vital_signs_vars = [
    "bp_systolic",
    "bp_diastolic",
    "heart_rate",
    "temperature",
    "respiratory_rate"
]

instrument = higher_level_agent.create_instrument(
    variables=vital_signs_vars,
    name="Vital Signs Assessment"
)

print(f"Instrument: {instrument['instrument_name']}")
print(f"Description: {instrument['description']}")
print(f"\n--- Markdown Documentation ---")
print(instrument['documentation_markdown'])
```

**Creating Codebook Overview:**
```python
# Generate complete codebook
all_variables = db.execute_query("SELECT * FROM parsed_fields")

codebook = higher_level_agent.generate_codebook(
    variables=all_variables,
    study_name="Diabetes Prevention Trial",
    version="2.0"
)

# Save codebook
with open("codebook_v2.md", 'w') as f:
    f.write(codebook['markdown'])

print(f"Codebook generated with {len(codebook['instruments'])} instruments")
```

**Auto-Grouping Variables:**
```python
# Let the agent intelligently group variables
auto_groups = higher_level_agent.auto_group_variables(all_variables)

for group in auto_groups:
    print(f"\nGroup: {group['name']}")
    print(f"  Variables: {', '.join(group['variables'])}")
    print(f"  Rationale: {group['grouping_rationale']}")
```

---

## Putting It All Together

### Advanced Workflow Example

```python
# Complete workflow with all advanced features

# 1. Initialize with configuration
config = APIConfig(tier="paid", requests_per_minute=60)
db = DatabaseManager("advanced_project.db")
db.connect()
db.initialize_schema()

orchestrator = Orchestrator(db)
version_agent = VersionControlAgent(db)
validator = ValidationAgent(config)
conventions_agent = DataConventionsAgent(config)
design_agent = DesignImprovementAgent(config)
higher_level_agent = HigherLevelDocumentationAgent(config)

# 2. Batch process multiple files
files = glob.glob("data_dictionaries/*.csv")
batch_processor = BatchProcessor(orchestrator)
results = batch_processor.process_batch(files, auto_approve=False)

# 3. Validate all outputs
for file_name, job_id in results.items():
    pending = orchestrator.review_queue.get_pending_items(job_id)

    for item in pending:
        # Validate each output
        validation = validator.process(item.generated_content)

        if validation['validation_passed']:
            # Check conventions
            conv_report = conventions_agent.process(item.generated_content)

            if conv_report['convention_compliance'] < 80:
                print(f"Convention issues in {file_name}: {conv_report['warnings']}")

            # Improve design
            improved = design_agent.process(item.generated_content)

            # Create version
            version_agent.create_version(
                element_id=item.item_id,
                element_type="review_item",
                content=improved['improved_content'],
                author="automated_improvement"
            )

            # Approve improved version
            orchestrator.review_queue.approve_item(
                item.item_id,
                approved_content=improved['improved_content']
            )
        else:
            print(f"Validation failed for item {item.item_id}")
            for issue in validation['issues_found']:
                print(f"  - {issue['description']}")

# 4. Generate higher-level documentation
for job_id in results.values():
    approved_items = db.execute_query(
        "SELECT * FROM ReviewQueue WHERE job_id = ? AND status = 'Approved'",
        (job_id,)
    )

    # Auto-group into instruments
    instruments = higher_level_agent.auto_group_variables(approved_items)

    # Generate final documentation with instruments
    final_doc = orchestrator.finalize_documentation(job_id)

    # Append instrument documentation
    for instrument in instruments:
        final_doc += f"\n\n{instrument['documentation_markdown']}"

print("Advanced workflow complete!")
```

---

## See Also

- [README.md](README.md) - Project overview
- [AGENTS.md](AGENTS.md) - Complete agent documentation
- [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) - Database tables
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Common code snippets

---

**Last Updated:** 2025-11-22
