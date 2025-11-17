# ADE Database Schema Documentation

Complete documentation of the SQLite database schema used by the Agent Development Environment (ADE) system.

---

## Overview

The ADE uses SQLite for persistent storage of:
- Agent configurations and prompts
- Context library (Toons)
- Processing jobs and status
- Human-in-the-loop review workflows
- Session history and memory
- System state and configuration

---

## Entity Relationship Diagram

```
┌─────────────┐         ┌─────────────┐
│   Agents    │         │    Jobs     │
└──────┬──────┘         └──────┬──────┘
       │                       │
       │                       │
       └───────────┬───────────┘
                   │
           ┌───────▼───────┐
           │  ReviewQueue  │
           └───────┬───────┘
                   │
       ┌───────────┼───────────┐
       │           │           │
┌──────▼──┐  ┌─────▼────┐  ┌───▼─────────┐
│  Toons  │  │ Session  │  │ SystemState │
│         │  │ History  │  │             │
└─────────┘  └──────────┘  └─────────────┘
```

---

## Core Tables

### 1. Agents

Stores agent definitions and system prompts.

```sql
CREATE TABLE IF NOT EXISTS Agents (
    agent_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    system_prompt TEXT NOT NULL,
    model_name TEXT DEFAULT 'gemini-2.0-flash-exp',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Fields:**

| Column | Type | Description |
|--------|------|-------------|
| `agent_id` | INTEGER | Primary key, auto-incremented |
| `name` | TEXT | Unique agent name (e.g., "DataParserAgent") |
| `system_prompt` | TEXT | System prompt defining agent behavior |
| `model_name` | TEXT | Gemini model to use (default: gemini-2.0-flash-exp) |
| `created_at` | TIMESTAMP | Creation timestamp |
| `updated_at` | TIMESTAMP | Last modification timestamp |

**Example Data:**
```sql
INSERT INTO Agents (name, system_prompt, model_name)
VALUES (
    'DataParserAgent',
    'You are a DataParserAgent specialized in parsing...',
    'gemini-2.0-flash-exp'
);
```

**Common Queries:**
```python
# Get agent by name
agent = db.execute_query(
    "SELECT * FROM Agents WHERE name = ?",
    ("DataParserAgent",)
)[0]

# Update system prompt
db.execute_query(
    "UPDATE Agents SET system_prompt = ?, updated_at = CURRENT_TIMESTAMP WHERE name = ?",
    (new_prompt, "DataParserAgent")
)

# List all agents
agents = db.execute_query("SELECT name, model_name FROM Agents ORDER BY name")
```

---

### 2. Toons

Context snippets library for agent enhancement.

```sql
CREATE TABLE IF NOT EXISTS Toons (
    toon_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    toon_type TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Fields:**

| Column | Type | Description |
|--------|------|-------------|
| `toon_id` | INTEGER | Primary key, auto-incremented |
| `name` | TEXT | Unique toon identifier name |
| `toon_type` | TEXT | Type of toon (see ToonType enum) |
| `content` | TEXT | Actual content of the toon |
| `metadata` | TEXT | JSON metadata (version, tags, etc.) |
| `created_at` | TIMESTAMP | Creation timestamp |
| `updated_at` | TIMESTAMP | Last modification timestamp |

**Toon Types (ToonType Enum):**
- `SUMMARY` - High-level summaries of large documents
- `CHUNK` - Specific logical pieces of documents
- `INSTRUCTION` - Reusable instructions for agents
- `VERSION` - Change descriptions and version notes
- `DESIGN` - Design decision rationale
- `MAPPING` - Saved mappings for automation

**Example Data:**
```sql
INSERT INTO Toons (name, toon_type, content, metadata)
VALUES (
    'OMOP_BP_Mapping',
    'INSTRUCTION',
    'Always map systolic BP to OMOP concept 3004249...',
    '{"standard": "OMOP", "validated": "2024-11-15"}'
);
```

**Common Queries:**
```python
# Get toon by name
toon = db.execute_query(
    "SELECT * FROM Toons WHERE name = ?",
    ("OMOP_BP_Mapping",)
)[0]

# List toons by type
instructions = db.execute_query(
    "SELECT * FROM Toons WHERE toon_type = ?",
    ("INSTRUCTION",)
)

# Search toons by content
matching = db.execute_query(
    "SELECT * FROM Toons WHERE content LIKE ?",
    ("%blood pressure%",)
)

# Get all toons with metadata parsing
import json
toons = db.execute_query("SELECT * FROM Toons")
for toon in toons:
    if toon['metadata']:
        toon['metadata'] = json.loads(toon['metadata'])
```

---

### 3. Jobs

Tracks processing jobs and their status.

```sql
CREATE TABLE IF NOT EXISTS Jobs (
    job_id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_file TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    metadata TEXT
);
```

**Fields:**

| Column | Type | Description |
|--------|------|-------------|
| `job_id` | INTEGER | Primary key, auto-incremented |
| `source_file` | TEXT | Name/path of source data file |
| `status` | TEXT | Current job status |
| `created_at` | TIMESTAMP | Job creation timestamp |
| `updated_at` | TIMESTAMP | Last status update |
| `completed_at` | TIMESTAMP | Completion timestamp (nullable) |
| `metadata` | TEXT | JSON metadata (config, stats, etc.) |

**Job Statuses:**
- `pending` - Job created, not started
- `processing` - Currently being processed
- `awaiting_review` - Human review required
- `completed` - Successfully completed
- `failed` - Processing failed
- `cancelled` - Manually cancelled

**Example Data:**
```sql
INSERT INTO Jobs (source_file, status, metadata)
VALUES (
    'diabetes_study.csv',
    'processing',
    '{"total_fields": 45, "auto_approve": false}'
);
```

**Common Queries:**
```python
# Get all jobs by status
pending_jobs = db.execute_query(
    "SELECT * FROM Jobs WHERE status = ?",
    ("pending",)
)

# Update job status
db.execute_query(
    """UPDATE Jobs
       SET status = ?, updated_at = CURRENT_TIMESTAMP
       WHERE job_id = ?""",
    ("completed", job_id)
)

# Mark job as completed
db.execute_query(
    """UPDATE Jobs
       SET status = 'completed',
           completed_at = CURRENT_TIMESTAMP,
           updated_at = CURRENT_TIMESTAMP
       WHERE job_id = ?""",
    (job_id,)
)

# Get job statistics
stats = db.execute_query("""
    SELECT status, COUNT(*) as count
    FROM Jobs
    GROUP BY status
""")
```

---

### 4. ReviewQueue

Central HITL (Human-in-the-Loop) workflow management.

```sql
CREATE TABLE IF NOT EXISTS ReviewQueue (
    item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL,
    source_agent TEXT NOT NULL,
    field_name TEXT,
    generated_content TEXT NOT NULL,
    status TEXT DEFAULT 'Pending',
    approved_content TEXT,
    reviewer_feedback TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES Jobs(job_id)
);
```

**Fields:**

| Column | Type | Description |
|--------|------|-------------|
| `item_id` | INTEGER | Primary key, auto-incremented |
| `job_id` | INTEGER | Foreign key to Jobs table |
| `source_agent` | TEXT | Agent that generated this content |
| `field_name` | TEXT | Field being documented (nullable) |
| `generated_content` | TEXT | AI-generated content for review |
| `status` | TEXT | Review status |
| `approved_content` | TEXT | Final approved content (nullable) |
| `reviewer_feedback` | TEXT | Reviewer notes/comments |
| `created_at` | TIMESTAMP | When item was added to queue |
| `reviewed_at` | TIMESTAMP | When item was reviewed |

**Review Statuses:**
- `Pending` - Awaiting human review
- `Approved` - Content approved (with or without edits)
- `Rejected` - Content rejected, needs regeneration
- `Needs_Clarification` - Agent needs more information

**Example Data:**
```sql
INSERT INTO ReviewQueue (job_id, source_agent, field_name, generated_content)
VALUES (
    1,
    'PlainLanguageAgent',
    'bp_systolic',
    '## Variable: bp_systolic\n\nBlood pressure measurement...'
);
```

**Common Queries:**
```python
# Get pending reviews for a job
pending = db.execute_query(
    """SELECT * FROM ReviewQueue
       WHERE job_id = ? AND status = 'Pending'
       ORDER BY created_at""",
    (job_id,)
)

# Approve an item
db.execute_query(
    """UPDATE ReviewQueue
       SET status = 'Approved',
           approved_content = ?,
           reviewed_at = CURRENT_TIMESTAMP
       WHERE item_id = ?""",
    (final_content, item_id)
)

# Reject with feedback
db.execute_query(
    """UPDATE ReviewQueue
       SET status = 'Rejected',
           reviewer_feedback = ?,
           reviewed_at = CURRENT_TIMESTAMP
       WHERE item_id = ?""",
    (feedback_text, item_id)
)

# Get items needing clarification
clarifications = db.execute_query(
    """SELECT * FROM ReviewQueue
       WHERE status = 'Needs_Clarification' AND job_id = ?""",
    (job_id,)
)

# Review statistics
stats = db.execute_query("""
    SELECT
        status,
        COUNT(*) as count,
        AVG(julianday(reviewed_at) - julianday(created_at)) as avg_review_days
    FROM ReviewQueue
    WHERE reviewed_at IS NOT NULL
    GROUP BY status
""")
```

---

### 5. SessionHistory

Chat logs and conversation history for context management.

```sql
CREATE TABLE IF NOT EXISTS SessionHistory (
    entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    token_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_compacted BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (job_id) REFERENCES Jobs(job_id)
);
```

**Fields:**

| Column | Type | Description |
|--------|------|-------------|
| `entry_id` | INTEGER | Primary key, auto-incremented |
| `job_id` | INTEGER | Associated job (nullable for global) |
| `role` | TEXT | Message role (user, assistant, system) |
| `content` | TEXT | Message content |
| `token_count` | INTEGER | Estimated token count |
| `created_at` | TIMESTAMP | When message was recorded |
| `is_compacted` | BOOLEAN | Whether this entry was compacted |

**Roles:**
- `user` - User messages/input
- `assistant` - Agent/system responses
- `system` - System messages/prompts

**Example Data:**
```sql
INSERT INTO SessionHistory (job_id, role, content, token_count)
VALUES (
    1,
    'user',
    'Please explain the HbA1c field in more detail',
    12
);
```

**Common Queries:**
```python
# Get session history for a job
history = db.execute_query(
    """SELECT role, content, created_at
       FROM SessionHistory
       WHERE job_id = ?
       ORDER BY created_at""",
    (job_id,)
)

# Calculate total tokens in context
token_stats = db.execute_query(
    """SELECT
         SUM(token_count) as total_tokens,
         COUNT(*) as message_count
       FROM SessionHistory
       WHERE job_id = ? AND is_compacted = FALSE""",
    (job_id,)
)[0]

# Mark entries as compacted
db.execute_query(
    """UPDATE SessionHistory
       SET is_compacted = TRUE
       WHERE job_id = ? AND is_compacted = FALSE""",
    (job_id,)
)

# Get recent messages
recent = db.execute_query(
    """SELECT * FROM SessionHistory
       WHERE job_id = ?
       ORDER BY created_at DESC
       LIMIT 10""",
    (job_id,)
)
```

---

### 6. SystemState

Application state persistence and configuration.

```sql
CREATE TABLE IF NOT EXISTS SystemState (
    state_id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Fields:**

| Column | Type | Description |
|--------|------|-------------|
| `state_id` | INTEGER | Primary key, auto-incremented |
| `key` | TEXT | State key identifier |
| `value` | TEXT | State value (often JSON) |
| `created_at` | TIMESTAMP | When state was created |
| `updated_at` | TIMESTAMP | Last update timestamp |

**Common State Keys:**
- `current_job_id` - Active job being processed
- `api_usage_today` - Daily API call counter
- `last_compaction` - Last context compaction timestamp
- `element:field:version` - Version tracking for elements
- `config:rate_limit` - Rate limiting configuration

**Example Data:**
```sql
INSERT INTO SystemState (key, value)
VALUES (
    'api_usage_today',
    '{"count": 42, "date": "2024-11-15"}'
);
```

**Common Queries:**
```python
# Get state value
state = db.execute_query(
    "SELECT value FROM SystemState WHERE key = ?",
    ("current_job_id",)
)
if state:
    current_job = state[0]['value']

# Set or update state
db.execute_query(
    """INSERT INTO SystemState (key, value)
       VALUES (?, ?)
       ON CONFLICT(key) DO UPDATE SET
         value = excluded.value,
         updated_at = CURRENT_TIMESTAMP""",
    (key, value)
)

# Get all configuration states
configs = db.execute_query(
    "SELECT key, value FROM SystemState WHERE key LIKE 'config:%'"
)

# Clean up old states
db.execute_query(
    """DELETE FROM SystemState
       WHERE key LIKE 'temp:%'
         AND updated_at < datetime('now', '-1 day')"""
)
```

---

## Database Initialization

The DatabaseManager class handles all database operations:

```python
class DatabaseManager:
    """
    Manages SQLite database connections and operations.
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.connection = None

    def connect(self):
        """Establish database connection."""
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row

    def initialize_schema(self):
        """Create all tables if they don't exist."""
        # Creates Agents, Toons, Jobs, ReviewQueue,
        # SessionHistory, and SystemState tables

    def execute_query(self, query: str, params: tuple = None):
        """Execute a query and return results."""
        cursor = self.connection.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        self.connection.commit()
        return [dict(row) for row in cursor.fetchall()]

    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
```

**Initialization Example:**
```python
db = DatabaseManager("project.db")
db.connect()
db.initialize_schema()

# Verify tables created
tables = db.execute_query(
    "SELECT name FROM sqlite_master WHERE type='table'"
)
print("Tables:", [t['name'] for t in tables])
```

---

## Indexes and Performance

For optimal performance, consider adding indexes:

```sql
-- Speed up job lookups
CREATE INDEX IF NOT EXISTS idx_jobs_status ON Jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_created ON Jobs(created_at);

-- Speed up review queue queries
CREATE INDEX IF NOT EXISTS idx_review_job ON ReviewQueue(job_id);
CREATE INDEX IF NOT EXISTS idx_review_status ON ReviewQueue(status);

-- Speed up session history retrieval
CREATE INDEX IF NOT EXISTS idx_session_job ON SessionHistory(job_id);
CREATE INDEX IF NOT EXISTS idx_session_compacted ON SessionHistory(is_compacted);

-- Speed up toon lookups
CREATE INDEX IF NOT EXISTS idx_toons_type ON Toons(toon_type);

-- Speed up state lookups
CREATE INDEX IF NOT EXISTS idx_state_key ON SystemState(key);
```

---

## Backup and Recovery

### Backup Database
```python
import shutil
from datetime import datetime

def backup_database(db_path: str, backup_dir: str = "."):
    """Create timestamped backup of database."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{backup_dir}/backup_{timestamp}.db"
    shutil.copy2(db_path, backup_path)
    return backup_path

backup_file = backup_database("project.db", "backups/")
print(f"Backup created: {backup_file}")
```

### Restore Database
```python
def restore_database(backup_path: str, db_path: str):
    """Restore database from backup."""
    shutil.copy2(backup_path, db_path)
    print(f"Restored {db_path} from {backup_path}")

restore_database("backups/backup_20241115_120000.db", "project.db")
```

### Export Data
```python
import json

def export_toons(db: DatabaseManager, output_file: str):
    """Export all toons to JSON."""
    toons = db.execute_query("SELECT * FROM Toons")
    with open(output_file, 'w') as f:
        json.dump(toons, f, indent=2, default=str)

export_toons(db, "toons_export.json")
```

---

## Data Integrity

### Foreign Key Enforcement
```python
# Enable foreign key constraints
db.execute_query("PRAGMA foreign_keys = ON")
```

### Data Validation
```python
def validate_review_item(item: dict) -> bool:
    """Validate review item before insertion."""
    required_fields = ['job_id', 'source_agent', 'generated_content']
    valid_statuses = ['Pending', 'Approved', 'Rejected', 'Needs_Clarification']

    for field in required_fields:
        if field not in item or not item[field]:
            return False

    if 'status' in item and item['status'] not in valid_statuses:
        return False

    return True
```

---

## Migrations

For schema updates, implement migration scripts:

```python
def migrate_v1_to_v2(db: DatabaseManager):
    """Example migration: Add metadata column to Jobs."""

    # Check if migration needed
    columns = db.execute_query("PRAGMA table_info(Jobs)")
    column_names = [col['name'] for col in columns]

    if 'metadata' not in column_names:
        db.execute_query(
            "ALTER TABLE Jobs ADD COLUMN metadata TEXT"
        )
        print("Migration complete: Added metadata column to Jobs")
    else:
        print("Migration not needed: metadata column exists")
```

---

## See Also

- [README.md](README.md) - Project overview
- [AGENTS.md](AGENTS.md) - Agent documentation
- [ADVANCED_FEATURES.md](ADVANCED_FEATURES.md) - Batch processing and validation
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Common code snippets

---

**Last Updated:** 2025-11-17
