# ADE Quick Reference Guide

Quick reference for common tasks and code snippets.

---

## 🚀 Getting Started

### Initialize System
```python
import sqlite3
from ade_system import *  # All classes from notebook

# Connect to database
db = DatabaseManager("project.db")
db.connect()
db.initialize_schema()

# Create orchestrator
orchestrator = Orchestrator(db)
```

---

## 📚 Toon Notation - Compact Data Encoding

### What is Toon Notation?

A compact format that reduces token usage by **40-70%** when passing data to LLMs.

```python
# Instead of verbose JSON:
data = {"items": [{"id": 1, "name": "foo"}, {"id": 2, "name": "bar"}]}
json_str = json.dumps(data)  # ~80 tokens

# Use Toon notation:
toon_str = ToonNotation.encode(data)  # ~25 tokens (70% savings!)
```

### Encode Data in Toon Notation

```python
# Simple object
data = {'id': 1, 'name': 'Ada'}
encoded = ToonNotation.encode(data)
# Output:
# id: 1
# name: Ada

# Tabular array (most efficient for uniform data!)
data = {
    'patients': [
        {'id': 1, 'age': 45, 'dx': 'diabetes'},
        {'id': 2, 'age': 52, 'dx': 'hypertension'}
    ]
}
encoded = ToonNotation.encode(data)
# Output:
# patients[2]{id,age,dx}:
#   1,45,diabetes
#   2,52,hypertension

# Primitive array (inline)
data = {'tags': ['foo', 'bar', 'baz']}
encoded = ToonNotation.encode(data)
# Output:
# tags[3]: foo,bar,baz
```

### Compare Token Usage

```python
# See the savings
comparison = ToonNotation.compare_sizes(your_data)
print(f"JSON: {comparison['json_tokens']} tokens")
print(f"Toon: {comparison['toon_tokens']} tokens")
print(f"Savings: {comparison['savings_percent']}%")
```

### Use with Agents

```python
# Pass data efficiently to agents
parsed_data = [{'var': 'bp_sys', 'type': 'int'}, ...]

# Option 1: JSON (verbose)
agent.process(json.dumps(parsed_data))  # Many tokens

# Option 2: Toon notation (efficient!)
agent.process(ToonNotation.encode(parsed_data))  # Fewer tokens
```

---

## 📝 Toon Library - Context Snippets

### Create a Toon
```python
toon_manager = ToonManager(db)

# Instruction toon
toon_id = toon_manager.create_toon(
    name="OMOP_BP_Mapping",
    toon_type=ToonType.INSTRUCTION,
    content="Always map systolic BP to OMOP concept 3004249"
)

# Design decision toon
toon_manager.create_toon(
    name="Study_Protocol_Notes",
    toon_type=ToonType.DESIGN,
    content="BP measured sitting, 5 min rest, appropriate cuff size"
)

# Mapping toon
toon_manager.create_toon(
    name="Sex_Code_Mapping",
    toon_type=ToonType.MAPPING,
    content='{"M": "8507", "F": "8532", "O": "8570"}',
    metadata={"standard": "OMOP", "field": "sex"}
)
```

### Get and Update Toons
```python
# Get by name
toon = toon_manager.get_toon_by_name("OMOP_BP_Mapping")

# Update content
toon_manager.update_toon(
    toon_id=toon.toon_id,
    content="Updated mapping rules...",
    metadata={"version": "2.0"}
)

# List all toons
all_toons = toon_manager.list_toons()

# List by type
instructions = toon_manager.list_toons(ToonType.INSTRUCTION)
```

### Inject Toons into Agents
```python
# Get relevant toons
toons = [
    toon_manager.get_toon_by_name("OMOP_BP_Mapping"),
    toon_manager.get_toon_by_name("Study_Protocol_Notes")
]

# Inject into agents
orchestrator.domain_ontology.inject_toons(toons)
orchestrator.plain_language.inject_toons(toons)
```

---

## 🔄 Processing Data

### Basic Processing
```python
# Your data dictionary as string
data_dict = """
Variable Name,Field Type,Field Label,Choices,Notes
patient_id,text,Patient ID,,Unique identifier
age,integer,Age (years),,
"""

# Process with auto-approval (for testing)
job_id = orchestrator.process_data_dictionary(
    source_data=data_dict,
    source_file="my_study.csv",
    auto_approve=True
)
```

### Processing with Manual Review
```python
# Process WITHOUT auto-approval
job_id = orchestrator.process_data_dictionary(
    source_data=data_dict,
    source_file="my_study.csv",
    auto_approve=False  # Human review required
)

# Review is covered in next section
```

### Processing from File
```python
# Read from CSV file
with open("data_dictionary.csv", 'r') as f:
    data_dict = f.read()

job_id = orchestrator.process_data_dictionary(
    source_data=data_dict,
    source_file="data_dictionary.csv",
    auto_approve=False
)
```

---

## ✅ Review Workflow

### Get Pending Reviews
```python
review_queue = orchestrator.review_queue

# All pending items
pending = review_queue.get_pending_items()

# Pending for specific job
pending = review_queue.get_pending_items(job_id)

# Display first item
if pending:
    item = pending[0]
    print(f"Item ID: {item.item_id}")
    print(f"Source Agent: {item.source_agent}")
    print(f"\nGenerated Content:\n{item.generated_content}")
```

### Approve Items
```python
# Approve without changes
review_queue.approve_item(item_id=42)

# Approve with edits
edited_content = """
## Variable: blood_pressure_systolic

[... generated content ...]

**Additional Notes:** Added by reviewer
"""
review_queue.approve_item(item_id=42, approved_content=edited_content)
```

### Reject Items
```python
review_queue.reject_item(
    item_id=42,
    feedback="Needs more clinical context about measurement protocol"
)
```

### Handle Clarifications
```python
# Get items needing clarification
clarification_items = review_queue.get_clarification_items(job_id)

for item in clarification_items:
    print(f"Question: {item.generated_content}")
    # User provides response
    response = "This field represents biological sex from medical records"

    # Submit clarification
    review_queue.submit_clarification(item.item_id, response)
```

---

## 📄 Generate Documentation

### Finalize Documentation
```python
# Generate final documentation from approved items
documentation = orchestrator.finalize_documentation(
    job_id=job_id,
    output_file="my_documentation.md"
)

# View the documentation
print(documentation[:500])  # First 500 chars
```

### Export Documentation
```python
# Already saved to file, can also:
with open("my_documentation.md", 'r') as f:
    doc_content = f.read()

# Display in Jupyter/Kaggle
from IPython.display import Markdown, display
display(Markdown(doc_content))

# Download link in Kaggle
from IPython.display import FileLink
FileLink("my_documentation.md")
```

---

## 🧠 Context Management

### Monitor Working Memory
```python
context_manager = ContextManager(db)

# Check memory status
memory = context_manager.get_working_memory(job_id)

print(f"Total tokens: {memory['total_tokens']}")
print(f"Active toons: {len(memory['active_toon_ids'])}")
print(f"Session messages: {len(memory['session_history'])}")
print(f"Needs compaction: {memory['needs_compaction']}")
```

### Compact Context
```python
# Manual compaction
if memory['needs_compaction']:
    summary = context_manager.compact_context(job_id)
    print(f"Created summary: {summary[:200]}...")
```

### Clear Working Memory
```python
# Clear context (preserves database)
context_manager.clear_context(job_id)
```

### Add to Session History
```python
# Log conversation
context_manager.add_to_session_history(
    job_id=job_id,
    role="user",
    content="Please explain the HbA1c field"
)

context_manager.add_to_session_history(
    job_id=job_id,
    role="assistant",
    content="HbA1c measures average blood glucose over 2-3 months..."
)
```

---

## 🔍 Query Database Directly

### Check Jobs
```python
jobs = db.execute_query("SELECT * FROM Jobs ORDER BY created_at DESC")
for job in jobs:
    print(f"{job['job_id']}: {job['source_file']} - {job['status']}")
```

### Check Review Queue Status
```python
stats = db.execute_query("""
    SELECT status, COUNT(*) as count
    FROM ReviewQueue
    GROUP BY status
""")
for stat in stats:
    print(f"{stat['status']}: {stat['count']}")
```

### Get All Approved Content
```python
approved = db.execute_query("""
    SELECT item_id, source_agent, approved_content
    FROM ReviewQueue
    WHERE status = 'Approved' AND job_id = ?
""", (job_id,))

for item in approved:
    print(f"\n--- Item {item['item_id']} ({item['source_agent']}) ---")
    print(item['approved_content'][:200])
```

---

## 🛠️ Custom Agents

### Create Custom Agent
```python
class MyCustomAgent(BaseAgent):
    def __init__(self):
        system_prompt = """
        You are a CustomAgent that does XYZ.

        Your task:
        1. Step one
        2. Step two

        Output format: JSON
        """
        super().__init__("MyCustomAgent", system_prompt)

    def custom_process(self, input_data):
        result = self.process(input_data)
        # Custom post-processing
        return result

# Use it
custom_agent = MyCustomAgent()
custom_agent.inject_toons(my_toons)
result = custom_agent.custom_process(my_data)
```

---

## 📊 Monitoring & Debugging

### System Status
```python
def display_system_status(db: DatabaseManager):
    print("=== ADE SYSTEM STATUS ===\n")

    # Jobs
    jobs = db.execute_query("SELECT * FROM Jobs")
    print(f"Jobs: {len(jobs)}")
    for job in jobs:
        print(f"  [{job['job_id']}] {job['status']}")

    # Toons
    toons = db.execute_query(
        "SELECT toon_type, COUNT(*) as count FROM Toons GROUP BY toon_type"
    )
    print(f"\nToon Library:")
    for toon in toons:
        print(f"  {toon['toon_type']}: {toon['count']}")

    # Review Queue
    reviews = db.execute_query(
        "SELECT status, COUNT(*) as count FROM ReviewQueue GROUP BY status"
    )
    print(f"\nReview Queue:")
    for review in reviews:
        print(f"  {review['status']}: {review['count']}")

display_system_status(db)
```

### Debug Agent Output
```python
# Test agent directly
agent = DataParserAgent()
result = agent.process(sample_data)
print(result)

# With toons injected
agent.inject_toons(my_toons)
prompt = agent.build_prompt(sample_data)
print("Full prompt being sent:")
print(prompt)
```

---

## 💾 Backup & Restore

### Backup Database
```python
import shutil
from datetime import datetime

# Create backup
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = f"project_backup_{timestamp}.db"
shutil.copy2("project.db", backup_path)
print(f"Backed up to {backup_path}")

# In Kaggle, copy to output directory
shutil.copy2("project.db", "/kaggle/working/project_backup.db")
```

### Restore Database
```python
# Restore from backup
shutil.copy2("project_backup_20241115_120000.db", "project.db")

# Reconnect
db.close()
db.connect()
```

---

## 🎯 Common Workflows

### Workflow 1: Quick Test
```python
# 1. Initialize
db = DatabaseManager("project.db")
db.connect()
db.initialize_schema()
orchestrator = Orchestrator(db)

# 2. Process with auto-approve
job_id = orchestrator.process_data_dictionary(
    source_data=my_data,
    source_file="test.csv",
    auto_approve=True
)

# 3. Get documentation
doc = orchestrator.finalize_documentation(job_id)
print(doc)
```

### Workflow 2: Production with Review
```python
# 1. Initialize and create toons
orchestrator = Orchestrator(db)
toon_manager = ToonManager(db)

# 2. Create domain-specific toons
toon_manager.create_toon(
    name="Project_Instructions",
    toon_type=ToonType.INSTRUCTION,
    content="Our specific mapping rules..."
)

# 3. Inject toons
toons = toon_manager.list_toons()
orchestrator.domain_ontology.inject_toons(toons)
orchestrator.plain_language.inject_toons(toons)

# 4. Process WITHOUT auto-approve
job_id = orchestrator.process_data_dictionary(
    source_data=my_data,
    source_file="study.csv",
    auto_approve=False
)

# 5. Review each item
pending = orchestrator.review_queue.get_pending_items(job_id)
for item in pending:
    print(f"\n{item.generated_content}")
    # Human decides: approve, edit, or reject
    orchestrator.review_queue.approve_item(item.item_id)

# 6. Handle clarifications
clarifications = orchestrator.review_queue.get_clarification_items(job_id)
for item in clarifications:
    print(f"Question: {item.generated_content}")
    response = input("Your response: ")
    orchestrator.review_queue.submit_clarification(item.item_id, response)

# 7. Generate final docs
doc = orchestrator.finalize_documentation(job_id, "final_docs.md")
```

### Workflow 3: Batch Processing
```python
# Process multiple files
files = ["study1.csv", "study2.csv", "study3.csv"]
job_ids = []

for file in files:
    with open(file, 'r') as f:
        data = f.read()

    job_id = orchestrator.process_data_dictionary(
        source_data=data,
        source_file=file,
        auto_approve=False
    )
    job_ids.append(job_id)
    print(f"Processed {file}: {job_id}")

# Review all at once
for job_id in job_ids:
    pending = orchestrator.review_queue.get_pending_items(job_id)
    # Review and approve...

# Generate all documentation
for job_id in job_ids:
    doc = orchestrator.finalize_documentation(
        job_id,
        f"documentation_{job_id}.md"
    )
```

---

## 🔧 Troubleshooting

### Error: "API key not valid"
```python
# Check if key is loaded
import os
print(os.environ.get('GOOGLE_API_KEY', 'NOT SET'))

# In Kaggle, verify secret exists
from kaggle_secrets import UserSecretsClient
user_secrets = UserSecretsClient()
try:
    key = user_secrets.get_secret("GOOGLE_API_KEY")
    print("✓ API key found")
except:
    print("✗ API key not found in secrets")
```

### Error: "Database is locked"
```python
# Close and reconnect
db.close()
db.connect()

# Or restart kernel and re-run
```

### Agent produces poor output
```python
# 1. Check system prompt
agent = TechnicalAnalyzerAgent()
print(agent.system_prompt)

# 2. Add more specific toons
toon_manager.create_toon(
    name="More_Specific_Instructions",
    toon_type=ToonType.INSTRUCTION,
    content="Be more specific about..."
)

# 3. Test with simpler input first
simple_data = '{"var": "test", "type": "integer"}'
result = agent.process(simple_data)
print(result)
```

---

## 📈 Performance Tips

1. **Use auto_approve for testing**: Much faster
2. **Create good toons early**: Reduces clarification requests
3. **Batch similar variables**: Process related fields together
4. **Monitor context size**: Compact when needed
5. **Reuse toons across jobs**: Build institutional knowledge

---

## 🎓 Best Practices

1. **Always backup before major changes**
   ```python
   shutil.copy2("project.db", "backup.db")
   ```

2. **Create toons for repeated patterns**
   ```python
   # Instead of clarifying same thing multiple times
   toon_manager.create_toon(name="CommonPattern", ...)
   ```

3. **Use descriptive job names**
   ```python
   job_id = orchestrator.create_job("diabetes_baseline_2024")
   ```

4. **Review and approve systematically**
   ```python
   # Review all, then approve all
   # Don't mix workflows
   ```

5. **Document your toons**
   ```python
   metadata = {
       "created_by": "PI",
       "purpose": "Standardize BP mapping",
       "validated": "2024-11-15"
   }
   ```

---

For more details, see:
- **README.md** - Full system documentation
- **PROJECT_OVERVIEW.md** - Architecture and rationale
- **KAGGLE_SETUP.md** - Kaggle-specific instructions
