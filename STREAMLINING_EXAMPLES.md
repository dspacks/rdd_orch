# ADE Notebook Streamlining - Usage Examples

This document provides practical examples of using the streamlined ADE features.

## Table of Contents

1. [Quick Start - New Users](#quick-start---new-users)
2. [Migration Examples - Existing Users](#migration-examples---existing-users)
3. [Extended Agent HITL Examples](#extended-agent-hitl-examples)
4. [Advanced Workflows](#advanced-workflows)
5. [Troubleshooting](#troubleshooting)

---

## Quick Start - New Users

### Example 1: Complete Workflow in 3 Cells

**Cell 1: Load Module**
```python
# Load the streamlining module
%run notebook_streamlining.py
```

**Cell 2: Initialize System**
```python
from notebook_streamlining import StreamlinedADE

# One-command initialization!
ade = StreamlinedADE()
ade.initialize()  # Auto-detects environment, loads API key, sets up database

# Create orchestrator (traditional way - for maximum flexibility)
orchestrator = Orchestrator(ade.db)  # Use ADE's database
ade.set_orchestrator(orchestrator)   # Connect to streamlined interface
```

**Cell 3: Show UI and Process Data**
```python
# Display the streamlined UI
ade.show_ui()

# Then use the UI to:
# 1. Upload your CSV/Excel/JSON file in "Upload & Process" tab
# 2. Click "Process Data Dictionary"
# 3. Switch to "Review & Approve" tab to review generated docs
# 4. Export approved documentation
```

**That's it! Three cells to go from zero to a complete HITL workflow.**

---

### Example 2: Programmatic Processing (No UI)

For users who prefer code over UI:

```python
# Load and initialize
%run notebook_streamlining.py
from notebook_streamlining import StreamlinedADE

ade = StreamlinedADE()
ade.initialize(show_ui=False)  # Skip UI display

# Create and connect orchestrator
orchestrator = Orchestrator(ade.db)
ade.set_orchestrator(orchestrator)

# Process file programmatically
job_id = ade.process_file(
    filename="my_healthcare_data.csv",
    auto_approve=False  # Require manual review
)

print(f"Job created: {job_id}")

# Manual review via code
pending = ade.review_queue.get_pending_items(job_id)
print(f"Pending items: {len(pending)}")

for item in pending:
    # Review content
    print(f"\nReviewing: {item.source_agent}")
    print(item.generated_content[:200] + "...")

    # Approve
    ade.review_queue.approve_item(item.item_id)
    print("✓ Approved")

# Get approved items
approved = ade.review_queue.get_approved_items(job_id)
print(f"\nTotal approved: {len(approved)}")
```

---

## Migration Examples - Existing Users

### Example 3: Full Migration (Recommended)

**Before:**
```python
# Old approach - 15+ cells

# Cell 1: Install
!pip install google-generativeai pandas ipywidgets

# Cell 2: Imports
import sqlite3
import json
import pandas as pd
import google.generativeai as genai
from dataclasses import dataclass
# ... many more imports

# Cell 3: API Configuration
api_key = userdata.get('GOOGLE_API_KEY')
genai.configure(api_key=api_key)

# Cell 4: Database Manager
class DatabaseManager:
    # ... 100+ lines ...

# Cell 5: Initialize Database
db = DatabaseManager("project.db")
db.connect()
db.initialize_schema()

# Cell 6: API Config
@dataclass
class APIConfig:
    # ... config code ...

# Cell 7-10: Agent classes
# ... 500+ lines of agent definitions ...

# Cell 11: Review Queue
class ReviewQueueManager:
    # ... 200+ lines ...

# Cell 12: Orchestrator
orchestrator = Orchestrator(db, api_config)

# Cell 13: File Upload
file_upload = widgets.FileUpload()
# ... file handling code ...

# Cell 14-15: Processing and Review
# ... manual processing code ...
```

**After:**
```python
# New approach - 3 cells

# Cell 1: Load
%run notebook_streamlining.py

# Cell 2: Initialize
from notebook_streamlining import StreamlinedADE
ade = StreamlinedADE()
ade.initialize()

# Cell 3: Connect and Show UI
orchestrator = Orchestrator(ade.db)
ade.set_orchestrator(orchestrator)
ade.show_ui()

# Everything else is handled by the UI!
```

**Reduction: 15 cells → 3 cells (80% reduction)**

---

### Example 4: Partial Migration (Keep Existing Setup)

If you want to keep your existing setup but add the streamlined UI:

```python
# Your existing cells 1-12 remain unchanged
# (database setup, orchestrator creation, etc.)

# Add new cell after your setup:
%run notebook_streamlining.py
from notebook_streamlining import StreamlinedADE

# Create ADE instance with existing components
ade = StreamlinedADE()
ade.db = db                          # Use your existing database
ade.set_orchestrator(orchestrator)    # Use your existing orchestrator
ade.initialized = True                # Mark as initialized

# Show streamlined UI
ade.show_ui()

# Now you have both:
# - Your existing code-based workflow
# - Streamlined UI for easier interaction
```

---

## Extended Agent HITL Examples

### Example 5: Validation Agent HITL

Process data with automatic validation and human review of flagged items:

```python
from notebook_streamlining import ExtendedAgentHITLIntegration

# Initialize HITL integration
hitl = ExtendedAgentHITLIntegration(orchestrator, review_queue)

# Process with validation HITL
job_id = hitl.process_with_validation_hitl(
    source_data=csv_data,
    source_file="patient_survey.csv",
    require_validation_approval=True  # Validation results go to review queue
)

# What happens:
# 1. Data processed through standard pipeline
# 2. ValidationAgent checks each generated doc
# 3. Items with validation_score < 80 flagged for review
# 4. Validation reports added to review queue
# 5. Human reviews validation findings
# 6. Human decides: approve/reject/fix

print(f"Job {job_id} processed with validation HITL")
print("Check 'Review & Approve' tab to see validation results")
```

**Example Validation Report in Review Queue:**
```markdown
# Validation Report

**Overall Score:** 65/100
**Status:** ❌ FAILED

## Issues Found:
- Missing required section: "Technical Details"
- Ontology mapping confidence < 70%
- Placeholder text detected: "[TBD]"
- Incomplete clinical context

## Recommendations:
- Add technical details section with data type and constraints
- Review ontology mappings for accuracy
- Replace placeholder text with actual content
- Expand clinical context with examples

## Original Content:
## Variable: patient_satisfaction

**Description:** Patient satisfaction score

[TBD - Add more details]
```

---

### Example 6: Design Improvement Agent HITL

Apply design improvements to approved documentation with human review:

```python
from notebook_streamlining import ExtendedAgentHITLIntegration

hitl = ExtendedAgentHITLIntegration(orchestrator, review_queue)

# First, process data normally
job_id = orchestrator.process_data_dictionary(
    source_data=csv_data,
    source_file="study_data.csv",
    auto_approve=False
)

# Review and approve initial documentation
# (use UI or code)

# Then apply design improvements with HITL
hitl.process_with_design_improvement_hitl(job_id)

# What happens:
# 1. Retrieves all approved documentation
# 2. DesignImprovementAgent analyzes each doc
# 3. Suggests design enhancements
# 4. Improvement reports added to review queue
# 5. Human reviews suggested improvements
# 6. If approved, improvements are applied

print("Design improvement suggestions added to review queue")
```

**Example Design Improvement Report:**
```markdown
# Design Improvement Report

**Design Score Before:** 70/100
**Design Score After:** 85/100
**Improvement:** +15 points

## Improvements Made:
1. Added structured sections for better readability
2. Enhanced clinical context with real-world examples
3. Improved table formatting for value ranges
4. Added visual separators between sections
5. Clarified technical terminology

## Comparison:

### Before:
## Variable: glucose_level
Glucose level in blood. Type: continuous. Range: 50-200 mg/dL.

### After:
## Variable: glucose_level

**Description:** Blood glucose concentration measurement

**Technical Details:**
- Data Type: Continuous (numeric)
- Unit: mg/dL (milligrams per deciliter)
- Valid Range: 50-200 mg/dL
- Precision: 1 decimal place

**Clinical Context:**
Fasting glucose levels help diagnose and monitor diabetes:
- Normal: 70-100 mg/dL
- Prediabetic: 100-125 mg/dL
- Diabetic: ≥126 mg/dL

**Example Values:**
- 85 mg/dL (normal fasting glucose)
- 110 mg/dL (elevated, prediabetic range)
- 150 mg/dL (hyperglycemia, requires medical attention)
```

---

### Example 7: Higher-Level Documentation Agent HITL

Generate instrument and segment documentation with human review:

```python
from notebook_streamlining import ExtendedAgentHITLIntegration

hitl = ExtendedAgentHITLIntegration(orchestrator, review_queue)

# Process and approve individual variable documentation first
job_id = orchestrator.process_data_dictionary(
    source_data=csv_data,
    source_file="clinical_trial.csv",
    auto_approve=False
)

# Review and approve all variables...

# Then generate higher-level documentation
hitl.process_with_higher_level_docs_hitl(job_id)

# What happens:
# 1. Analyzes all approved variable documentation
# 2. Groups related variables into instruments/segments
# 3. Generates instrument-level documentation
# 4. Adds instrument docs to review queue for approval
# 5. Human reviews groupings and documentation

print("Instrument documentation added to review queue")
```

**Example Instrument Documentation Report:**
```markdown
# Instrument Documentation

**Instrument Name:** bp_instrument
**Variables:** 3

## Variables Included:
- bp_systolic (Systolic Blood Pressure)
- bp_diastolic (Diastolic Blood Pressure)
- bp_method (Measurement Method)

## Instrument Description:

This instrument captures comprehensive blood pressure measurements
for cardiovascular assessment. It includes both systolic and diastolic
values along with the measurement method to ensure data quality and
enable proper interpretation.

### Purpose:
Blood pressure monitoring is essential for:
- Cardiovascular disease screening
- Hypertension diagnosis and management
- Treatment efficacy assessment
- Risk stratification

### Data Collection:
All three variables should be collected together during each blood
pressure measurement to maintain data integrity and enable complete
cardiovascular assessment.

### Quality Assurance:
- bp_method should always be recorded to validate measurement accuracy
- Both systolic and diastolic values required for complete assessment
- Values should be verified if outside expected ranges (70-200 mmHg)

### Clinical Interpretation:
| Systolic | Diastolic | Category |
|----------|-----------|----------|
| <120 | <80 | Normal |
| 120-129 | <80 | Elevated |
| 130-139 | 80-89 | Stage 1 Hypertension |
| ≥140 | ≥90 | Stage 2 Hypertension |

## Related Instruments:
- cardiovascular_risk_instrument
- vital_signs_instrument
```

---

### Example 8: Combined Extended Agent Workflow

Complete workflow using all extended agents with HITL:

```python
from notebook_streamlining import ExtendedAgentHITLIntegration

hitl = ExtendedAgentHITLIntegration(orchestrator, review_queue)

# Load your data
csv_data = pd.read_csv("comprehensive_study.csv").to_csv(index=False)

print("=" * 60)
print("COMPREHENSIVE HITL WORKFLOW")
print("=" * 60)

# Step 1: Process with validation
print("\n📋 Step 1: Processing with Validation HITL...")
job_id = hitl.process_with_validation_hitl(
    source_data=csv_data,
    source_file="comprehensive_study.csv",
    require_validation_approval=True
)

print(f"✓ Job {job_id} created")
print(f"✓ Documentation generated and validated")
print(f"👉 Review validation reports in 'Review & Approve' tab")
print(f"   Approve items that pass validation")
print(f"   Edit and fix items flagged by validation")

# Wait for user to review validation reports
input("\nPress Enter after reviewing validation reports...")

# Step 2: Apply design improvements
print("\n🎨 Step 2: Applying Design Improvements...")
hitl.process_with_design_improvement_hitl(job_id)

print(f"✓ Design improvement suggestions generated")
print(f"👉 Review design improvements in 'Review & Approve' tab")
print(f"   Approve improvements you want to apply")
print(f"   Reject to keep original formatting")

# Wait for user to review design improvements
input("\nPress Enter after reviewing design improvements...")

# Step 3: Generate higher-level documentation
print("\n📚 Step 3: Generating Higher-Level Documentation...")
hitl.process_with_higher_level_docs_hitl(job_id)

print(f"✓ Instrument and segment documentation generated")
print(f"👉 Review instrument docs in 'Review & Approve' tab")
print(f"   Verify variable groupings make sense")
print(f"   Approve instrument documentation")

print("\n" + "=" * 60)
print("WORKFLOW COMPLETE!")
print("=" * 60)
print(f"\nJob ID: {job_id}")
print(f"Next: Export final documentation once all items approved")
```

---

## Advanced Workflows

### Example 9: Batch Processing with HITL

Process multiple files with comprehensive HITL:

```python
from notebook_streamlining import StreamlinedADE, ExtendedAgentHITLIntegration

# Initialize
ade = StreamlinedADE()
ade.initialize(show_ui=False)
orchestrator = Orchestrator(ade.db)
ade.set_orchestrator(orchestrator)

hitl = ExtendedAgentHITLIntegration(orchestrator, review_queue)

# List of files to process
files = [
    "patient_demographics.csv",
    "lab_results.csv",
    "vital_signs.csv",
    "medications.csv"
]

job_ids = []

# Process each file with validation HITL
for filename in files:
    print(f"\nProcessing {filename}...")

    data = pd.read_csv(filename).to_csv(index=False)

    job_id = hitl.process_with_validation_hitl(
        source_data=data,
        source_file=filename,
        require_validation_approval=True
    )

    job_ids.append(job_id)
    print(f"✓ Job {job_id} created")

print(f"\n{'='*60}")
print(f"Batch processing complete!")
print(f"Created {len(job_ids)} jobs")
print(f"{'='*60}")

# Review all jobs
for job_id in job_ids:
    pending = review_queue.get_pending_items(job_id)
    print(f"\nJob {job_id}: {len(pending)} items pending review")

# Show UI for review
ade.show_ui()
```

---

### Example 10: Custom Validation Thresholds

Adjust validation strictness based on your needs:

```python
# Strict validation (high quality threshold)
def process_with_strict_validation(data, filename):
    job_id = orchestrator.create_job(filename)

    # Process normally
    parsed_data = orchestrator.data_parser.parse_csv(data)
    analyzed_data = orchestrator.technical_analyzer.analyze(parsed_data)

    for var_data in analyzed_data:
        ontology_result = orchestrator.domain_ontology.map_ontologies(var_data)
        enriched_data = {**var_data, **ontology_result}
        documentation = orchestrator.plain_language.document_variable(enriched_data)

        # Validate
        validation_result = orchestrator.validation.process(documentation)

        # Parse result
        if "```json" in validation_result:
            validation_result = validation_result.split("```json")[1].split("```")[0]

        validation_data = json.loads(validation_result)
        validation_score = validation_data.get('overall_score', 0)

        # Strict threshold: flag anything below 90
        if validation_score < 90:
            # Add to review queue with validation report
            review_queue.add_item(
                job_id=job_id,
                source_agent="ValidationAgent",
                source_data=json.dumps(enriched_data),
                generated_content=f"Validation Score: {validation_score}\n\n{documentation}"
            )
        else:
            # Auto-approve high-quality docs
            item_id = review_queue.add_item(
                job_id=job_id,
                source_agent="PlainLanguageAgent",
                source_data=json.dumps(enriched_data),
                generated_content=documentation
            )
            review_queue.approve_item(item_id)

    return job_id

# Use strict validation
job_id = process_with_strict_validation(csv_data, "critical_study.csv")
```

---

### Example 11: Environment-Specific Configuration

Customize based on runtime environment:

```python
from notebook_streamlining import StreamlinedADE

# Initialize
ade = StreamlinedADE()

# Check detected environment
if ade.environment == "kaggle":
    print("Running in Kaggle")
    # Kaggle-specific settings
    ade.initialize(show_ui=True)  # Show UI in Kaggle

elif ade.environment == "colab":
    print("Running in Google Colab")
    # Colab-specific settings
    ade.initialize(show_ui=True)

elif ade.environment == "local":
    print("Running locally")
    # Local-specific settings
    ade.initialize(show_ui=False)  # CLI workflow for local

    # Process files from command line args
    import sys
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        orchestrator = Orchestrator(ade.db)
        ade.set_orchestrator(orchestrator)
        job_id = ade.process_file(filename)
        print(f"Processed {filename} -> Job {job_id}")
```

---

## Troubleshooting

### Issue 1: API Key Not Found

**Error:**
```
ValueError: API key not found. Please provide via:
  1. StreamlinedADE(api_key='your-key')
  2. Environment variable: GOOGLE_API_KEY
  3. Kaggle Secrets / Colab Userdata
```

**Solution:**

**Option A: Pass directly**
```python
ade = StreamlinedADE(api_key="YOUR_API_KEY_HERE")
ade.initialize()
```

**Option B: Set environment variable**
```python
import os
os.environ['GOOGLE_API_KEY'] = "YOUR_API_KEY_HERE"

ade = StreamlinedADE()
ade.initialize()
```

**Option C: Use Kaggle Secrets (in Kaggle)**
1. Go to notebook Settings → Secrets
2. Add secret named `GOOGLE_API_KEY`
3. Restart kernel and run again

**Option D: Use Colab Userdata (in Colab)**
```python
from google.colab import userdata
userdata.set('GOOGLE_API_KEY', 'YOUR_API_KEY_HERE')

# Then run normally
ade = StreamlinedADE()
ade.initialize()
```

---

### Issue 2: Orchestrator Not Connected

**Error:**
```
Orchestrator not connected. Call set_orchestrator() first
```

**Solution:**
```python
# Create orchestrator first
orchestrator = Orchestrator(ade.db)

# Then connect it
ade.set_orchestrator(orchestrator)

# Now you can process files
job_id = ade.process_file("data.csv")
```

---

### Issue 3: File Upload Fails

**Error:**
```
File 'large_file.csv' is too large (75.2 MB). Maximum allowed size is 50 MB.
```

**Solution:**

**Option A: Split the file**
```python
# Split large file into smaller chunks
df = pd.read_csv("large_file.csv")

# Split into chunks of 10000 rows
chunk_size = 10000
for i in range(0, len(df), chunk_size):
    chunk = df.iloc[i:i+chunk_size]
    chunk.to_csv(f"chunk_{i//chunk_size}.csv", index=False)
    print(f"Created chunk_{i//chunk_size}.csv")

# Process each chunk
for i in range(len(df) // chunk_size + 1):
    job_id = ade.process_file(f"chunk_{i}.csv")
    print(f"Processed chunk_{i}.csv -> Job {job_id}")
```

**Option B: Increase size limit** (not recommended)
```python
from hitl_fixes import SafeDocumentUploader

# Create uploader with larger limit
uploader = SafeDocumentUploader(max_file_size_mb=100)

# Use custom processing
# (manual file upload and processing code)
```

---

### Issue 4: Review Queue Empty

**Problem:** No items appear in review queue after processing

**Check 1:** Verify job was created
```python
# Check if job exists
jobs = ade.db.execute_query(
    "SELECT * FROM Jobs WHERE job_id = ?",
    (job_id,)
)
print(jobs)
```

**Check 2:** Check review queue
```python
# Check all items for job
all_items = ade.db.execute_query(
    "SELECT * FROM ReviewQueue WHERE job_id = ?",
    (job_id,)
)
print(f"Total items: {len(all_items)}")

# Check pending items
pending = review_queue.get_pending_items(job_id)
print(f"Pending: {len(pending)}")

# Check approved items
approved = review_queue.get_approved_items(job_id)
print(f"Approved: {len(approved)}")
```

**Check 3:** Verify auto_approve setting
```python
# If you used auto_approve=True, items are automatically approved
# Use auto_approve=False to require manual review

job_id = ade.process_file("data.csv", auto_approve=False)  # Force manual review
```

---

### Issue 5: Extended Agent HITL Not Working

**Problem:** Extended agent outputs not appearing in review queue

**Solution:** Verify extended agents are initialized
```python
# Check if extended agents exist
print("Extended agents:")
print(f"  Validation: {orchestrator.validation}")
print(f"  Design Improvement: {orchestrator.design_improvement}")
print(f"  Higher Level Docs: {orchestrator.higher_level_docs}")

# If any are None, reinitialize orchestrator
orchestrator = Orchestrator(ade.db)
ade.set_orchestrator(orchestrator)

# Then try again
hitl = ExtendedAgentHITLIntegration(orchestrator, review_queue)
job_id = hitl.process_with_validation_hitl(data, "file.csv")
```

---

## Additional Resources

- **Full Documentation:** [STREAMLINING_ANALYSIS.md](STREAMLINING_ANALYSIS.md)
- **Repository README:** [README.md](README.md)
- **Project Overview:** [docs/PROJECT_OVERVIEW.md](docs/PROJECT_OVERVIEW.md)
- **Quick Reference:** [docs/QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md)

---

**Last Updated:** 2025-11-22
