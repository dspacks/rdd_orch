# Vertex AI Agent Engine Deployment Guide

**Last Updated:** 2025-11-22
**ADE Version:** 2.0

This guide provides comprehensive instructions for deploying the Healthcare Data Documentation Agent to Google Cloud's Vertex AI Agent Engine for production use.

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Deployment Structure](#deployment-structure)
4. [Extended Agent Capabilities](#extended-agent-capabilities)
5. [Deployment Files](#deployment-files)
6. [Deployment Steps](#deployment-steps)
7. [Testing the Deployed Agent](#testing-the-deployed-agent)
8. [Production Considerations](#production-considerations)
9. [Monitoring and Observability](#monitoring-and-observability)
10. [Troubleshooting](#troubleshooting)
11. [Cost Optimization](#cost-optimization)
12. [Cleanup](#cleanup)

---

## Overview

Vertex AI Agent Engine provides:

- ✅ **Fully managed infrastructure** with auto-scaling
- ✅ **Built-in security** with IAM integration
- ✅ **Production monitoring** through Cloud Console
- ✅ **Session and memory services** at scale
- ✅ **High availability** across regions
- ✅ **Automatic containerization** via ADK CLI
- ✅ **Zero-downtime deployments** with versioning

### Why Vertex AI Agent Engine?

1. **No Infrastructure Management**: Focus on agent logic, not DevOps
2. **Auto-scaling**: Handles traffic spikes automatically
3. **Enterprise Security**: HIPAA-compliant, SOC 2, ISO 27001 certified
4. **Cost-Effective**: Pay only for what you use (min_instances: 0)
5. **Integrated Monitoring**: Cloud Logging, Cloud Monitoring built-in

---

## Prerequisites

### 1. Google Cloud Project Setup

```bash
# Set your project ID
export PROJECT_ID="your-project-id"
export REGION="us-central1"

# Enable required APIs
gcloud services enable \
  aiplatform.googleapis.com \
  containerregistry.googleapis.com \
  cloudbuild.googleapis.com
```

### 2. Install ADK CLI

```bash
pip install google-adk
```

### 3. Authenticate with Google Cloud

```bash
gcloud auth login
gcloud config set project $PROJECT_ID
gcloud auth application-default login
```

### 4. IAM Permissions

Required roles for deployment:
- `roles/aiplatform.user`
- `roles/storage.objectAdmin`
- `roles/containerregistry.ServiceAgent`
- `roles/cloudbuild.builds.editor`

```bash
# Grant permissions to your account
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="user:your-email@example.com" \
    --role="roles/aiplatform.user"
```

---

## Deployment Structure

The deployment follows ADK conventions with the following structure:

```
healthcare_agent_deploy/
├── agent.py                     # Main agent logic with extended capabilities
├── requirements.txt             # Python dependencies
├── .env                         # Environment configuration
└── .agent_engine_config.json    # Deployment specifications
```

### File Purposes

| File | Purpose |
|------|---------|
| `agent.py` | Contains the `root_agent` with all tools and instructions |
| `requirements.txt` | Lists Python packages needed for the agent |
| `.env` | Environment variables (project ID, location, settings) |
| `.agent_engine_config.json` | Resource limits, scaling, and timeout configurations |

---

## Extended Agent Capabilities

The deployed agent includes **16 specialized tools** across 6 categories:

### 1. Core Healthcare Documentation Tools (3 tools)

- `parse_data_dictionary` - Parse CSV/JSON data dictionaries
- `map_to_ontology` - Map to OMOP, LOINC, SNOMED codes
- `generate_documentation` - Create human-readable docs

### 2. Design Improvement Tools (2 tools)

- `improve_document_design` - Enhance structure and readability
- `analyze_design_patterns` - Identify design inconsistencies

**NEW in v2.0**: Provides measurable design quality scores (readability, scannability, consistency, accessibility)

### 3. Data Conventions Tools (2 tools)

- `analyze_variable_conventions` - Detect naming patterns (snake_case, camelCase, etc.)
- `generate_conventions_glossary` - Create standards documentation

**NEW in v2.0**: Ensures consistency across large codebooks

### 4. Version Control Tools (4 tools)

- `create_version` - Track changes with semantic versioning
- `get_version_history` - View complete version history
- `rollback_version` - Revert to previous versions
- `compare_versions` - Diff between versions

**NEW in v2.0**: Full Git-like version management for documentation

### 5. Higher-Level Documentation Tools (4 tools)

- `identify_instruments` - Auto-detect measurement scales (e.g., PHQ-9, GAD-7)
- `document_instrument` - Create instrument-level documentation
- `document_segment` - Document logical variable groupings
- `generate_codebook_overview` - Comprehensive codebook summary

**NEW in v2.0**: Understands hierarchical data structure

### 6. Memory Tools (2 tools)

- `save_to_memory` - Store findings across sessions
- `retrieve_from_memory` - Recall previous learnings

**NEW in v2.0**: Session state persistence via ADK

---

## Deployment Files

### 1. agent.py

The main agent file includes:

```python
import os
import json
import hashlib
from datetime import datetime
import vertexai
from google.adk.agents import Agent, LlmAgent
from google.adk.tools.tool_context import ToolContext
from typing import Dict, List, Any, Optional

# Initialize Vertex AI
vertexai.init(
    project=os.environ.get("GOOGLE_CLOUD_PROJECT"),
    location=os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1"),
)

# ... [All 16 tool functions] ...

# Create the root agent
root_agent = LlmAgent(
    name="healthcare_documentation_agent",
    model="gemini-2.5-flash-lite",
    description="Advanced agent for healthcare data documentation with design improvement, conventions enforcement, version control, and higher-level documentation capabilities",
    instruction="""You are an Advanced Healthcare Data Documentation Agent with extended capabilities:

CORE CAPABILITIES:
1. Parse data dictionaries from various formats
2. Map variables to standard healthcare ontologies (OMOP, LOINC, SNOMED)
3. Generate clear, comprehensive documentation

EXTENDED CAPABILITIES:
4. **Design Improvement**: Enhance document structure, readability, and visual hierarchy
5. **Data Conventions**: Ensure variable naming standards and coding schemes are documented
6. **Version Control**: Track changes, manage versions, and support rollbacks
7. **Higher-Level Documentation**: Document instruments, segments, and codebook structures

WORKFLOW:
When processing a data dictionary:
1. Use parse_data_dictionary to extract variable information
2. Use map_to_ontology for each variable to find standard codes
3. Use analyze_variable_conventions to ensure naming standards are documented
4. Use generate_documentation to create human-readable documentation
5. Use improve_document_design to enhance the output quality
6. Use create_version to track changes and enable rollback
7. Use identify_instruments to find related variable groups
8. Use document_instrument for higher-level documentation
9. Use generate_codebook_overview for comprehensive summary

For updates and modifications:
- Always use create_version before making changes
- Use compare_versions to understand differences
- Use rollback_version if needed to revert changes

Remember to save important findings to memory for cross-session knowledge.""",
    tools=[
        # Core tools
        parse_data_dictionary,
        map_to_ontology,
        generate_documentation,
        # Design improvement tools
        improve_document_design,
        analyze_design_patterns,
        # Data conventions tools
        analyze_variable_conventions,
        generate_conventions_glossary,
        # Version control tools
        create_version,
        get_version_history,
        rollback_version,
        compare_versions,
        # Higher-level documentation tools
        identify_instruments,
        document_instrument,
        document_segment,
        generate_codebook_overview,
        # Memory tools
        save_to_memory,
        retrieve_from_memory,
    ],
)
```

**Full Implementation**: See `healthcare_agent_deploy/agent.py` after running the notebook cell

### 2. requirements.txt

```txt
google-adk>=1.0.0
google-cloud-aiplatform>=1.38.0
opentelemetry-instrumentation-google-genai
vertexai
```

### 3. .env

```bash
# Vertex AI Configuration
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_GENAI_USE_VERTEXAI=1
```

⚠️ **Important**: Update `GOOGLE_CLOUD_PROJECT` with your actual project ID

### 4. .agent_engine_config.json

```json
{
  "min_instances": 0,
  "max_instances": 3,
  "resource_limits": {
    "cpu": "2",
    "memory": "4Gi"
  },
  "timeout_seconds": 300,
  "environment_variables": {
    "LOG_LEVEL": "INFO"
  }
}
```

**Configuration Explained**:
- `min_instances: 0` - Scale to zero when idle (cost savings)
- `max_instances: 3` - Handle up to 3 concurrent requests
- `cpu: "2"` - 2 vCPUs per instance
- `memory: "4Gi"` - 4GB RAM per instance (handles large codebooks)
- `timeout_seconds: 300` - 5 minute timeout (allows complex processing)

---

## Deployment Steps

### Step 1: Generate Deployment Files

Run the deployment cell in the ADE notebook (Section 13):

```python
import os
import json

DEPLOY_DIR = "healthcare_agent_deploy"
os.makedirs(DEPLOY_DIR, exist_ok=True)

# ... (cells create all 4 files) ...
```

This creates the complete `healthcare_agent_deploy/` directory.

### Step 2: Update Configuration

```bash
cd healthcare_agent_deploy
# Edit .env file
nano .env
# Replace "your-project-id" with your actual project ID
```

### Step 3: Deploy Using ADK CLI

```bash
# From the parent directory (rdd_orch/)
adk deploy agent_engine \
    --project=$PROJECT_ID \
    --region=$REGION \
    healthcare_agent_deploy \
    --agent_engine_config_file=healthcare_agent_deploy/.agent_engine_config.json
```

**Deployment Process** (takes 3-5 minutes):

1. ✅ Validates agent code and dependencies
2. ✅ Builds container image with all tools
3. ✅ Pushes to Google Container Registry
4. ✅ Creates Agent Engine instance
5. ✅ Registers agent with Vertex AI

**Expected Output**:

```
Deploying agent to Vertex AI Agent Engine...
Building container image...
Pushing to Container Registry...
Creating Agent Engine instance...
✓ Agent deployed successfully!

Resource name: projects/YOUR_PROJECT/locations/REGION/agents/AGENT_ID
Agent URL: https://console.cloud.google.com/vertex-ai/agents/AGENT_ID
```

**Save the resource name** - you'll need it for testing and cleanup.

---

## Testing the Deployed Agent

### Method 1: Python SDK (Recommended)

```python
import vertexai
from vertexai import agent_engines

PROJECT_ID = "your-project-id"
REGION = "us-central1"

vertexai.init(project=PROJECT_ID, location=REGION)

# List deployed agents
agents_list = list(agent_engines.list())
print(f"Found {len(agents_list)} deployed agents")

if agents_list:
    remote_agent = agents_list[0]
    print(f"Agent: {remote_agent.display_name}")
    print(f"Resource: {remote_agent.resource_name}")

    # Test with sample data dictionary
    test_data = """Variable Name,Field Type,Field Label,Notes
patient_id,text,Patient ID,Unique identifier
age,integer,Age (years),Age at enrollment
sex,radio,Biological Sex,"1=Male, 2=Female"
bp_systolic,integer,Systolic BP,mmHg
bp_diastolic,integer,Diastolic BP,mmHg
hba1c,decimal,HbA1c (%),Glycemic control marker"""

    print("\n🧪 Testing agent with sample data dictionary...")

    # Synchronous query
    response = remote_agent.query(
        message=f"Parse this data dictionary and provide comprehensive documentation:\n\n{test_data}",
        user_id="test_user_001",
    )

    print("\n📋 Agent Response:")
    print(response)
```

### Method 2: Async Streaming (Production)

```python
import asyncio

async def test_agent_async():
    remote_agent = agents_list[0]

    async for item in remote_agent.async_stream_query(
        message="Identify any instruments in this dataset and document them.",
        user_id="user_42",
    ):
        if hasattr(item, 'text'):
            print(item.text, end='', flush=True)

asyncio.run(test_agent_async())
```

### Method 3: Cloud Console (Visual)

1. Navigate to [Vertex AI Agents](https://console.cloud.google.com/vertex-ai/agents)
2. Select your deployed agent
3. Click "Test Agent"
4. Enter test query in chat interface
5. View responses and tool calls

### Example Test Scenarios

**Test 1: Basic Parsing**
```
Query: "Parse this data dictionary: patient_id,text,Patient ID"
Expected: Successful parsing with structured output
```

**Test 2: Ontology Mapping**
```
Query: "Map the variable 'hba1c' to standard ontologies"
Expected: OMOP concept_id 3004410, LOINC code 4548-4
```

**Test 3: Design Improvement**
```
Query: "Improve the documentation design for this variable: age,integer,Age"
Expected: Enhanced markdown with proper headers and formatting
```

**Test 4: Instrument Detection**
```
Query: "Identify instruments in this dataset with variables: phq9_q1, phq9_q2, phq9_q3, gad7_q1, gad7_q2"
Expected: Two instruments detected (PHQ-9 and GAD-7)
```

**Test 5: Version Control**
```
Query: "Create a version for the patient_id documentation"
Expected: Version 1.0.0 created with content hash
```

---

## Production Considerations

### 1. Authentication & Security

**Service Accounts** (Recommended for Production):

```bash
# Create service account
gcloud iam service-accounts create healthcare-agent-sa \
    --display-name="Healthcare Agent Service Account"

# Grant minimum required permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:healthcare-agent-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"
```

**VPC Service Controls** (HIPAA Compliance):

```bash
# Create service perimeter for sensitive data
gcloud access-context-manager perimeters create healthcare_perimeter \
    --resources=projects/$PROJECT_ID \
    --restricted-services=aiplatform.googleapis.com
```

**Cloud Armor** (DDoS Protection):

```bash
# Create security policy
gcloud compute security-policies create agent-protection \
    --description="DDoS protection for agent endpoints"
```

### 2. Scaling Configuration

**Development Environment**:
```json
{
  "min_instances": 0,
  "max_instances": 1,
  "resource_limits": {
    "cpu": "1",
    "memory": "2Gi"
  }
}
```

**Production Environment**:
```json
{
  "min_instances": 1,
  "max_instances": 10,
  "resource_limits": {
    "cpu": "4",
    "memory": "8Gi"
  },
  "timeout_seconds": 600
}
```

**High-Traffic Environment**:
```json
{
  "min_instances": 3,
  "max_instances": 50,
  "resource_limits": {
    "cpu": "8",
    "memory": "16Gi"
  },
  "timeout_seconds": 300
}
```

### 3. Database Connections

For persistent storage, use Cloud SQL:

```python
# Add to agent.py
import sqlalchemy
from google.cloud.sql.connector import Connector

def get_db_connection():
    connector = Connector()
    conn = connector.connect(
        "PROJECT:REGION:INSTANCE",
        "pg8000",
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        db=os.environ["DB_NAME"]
    )
    return conn

# Update tools to use Cloud SQL instead of SQLite
```

### 4. Data Compliance (HIPAA/GDPR)

**PHI Handling**:
```python
# Add PHI detection
def contains_phi(text: str) -> bool:
    """Detect potential PHI in text."""
    phi_patterns = [
        r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
        r'\b\d{10}\b',  # Phone number
        r'\b[A-Z]{2}\d{6}\b',  # MRN
    ]
    import re
    return any(re.search(pattern, text) for pattern in phi_patterns)

# Add to tool functions
def parse_data_dictionary(data: str) -> Dict[str, Any]:
    if contains_phi(data):
        return {"status": "error", "message": "PHI detected, cannot process"}
    # ... rest of logic
```

**Audit Logging**:
```python
# Add to agent.py
import logging
from google.cloud import logging as cloud_logging

client = cloud_logging.Client()
logger = client.logger("healthcare-agent-audit")

def log_action(action: str, user_id: str, details: dict):
    logger.log_struct({
        "action": action,
        "user_id": user_id,
        "timestamp": datetime.now().isoformat(),
        "details": details
    })
```

---

## Monitoring and Observability

### 1. Cloud Logging

**View agent logs**:
```bash
gcloud logging read "resource.type=aiplatform.googleapis.com/Agent" \
    --limit 50 \
    --format json
```

**Filter by error**:
```bash
gcloud logging read "severity>=ERROR AND resource.type=aiplatform.googleapis.com/Agent" \
    --limit 10
```

### 2. Cloud Monitoring

**Create alert for error rate**:
```bash
gcloud alpha monitoring policies create \
    --notification-channels=CHANNEL_ID \
    --display-name="Agent Error Rate" \
    --condition-display-name="High Error Rate" \
    --condition-threshold-value=0.05 \
    --condition-threshold-duration=300s
```

### 3. Custom Metrics

Add to `agent.py`:
```python
from google.cloud import monitoring_v3
import time

client = monitoring_v3.MetricServiceClient()
project_name = f"projects/{os.environ['GOOGLE_CLOUD_PROJECT']}"

def record_metric(metric_type: str, value: float):
    series = monitoring_v3.TimeSeries()
    series.metric.type = f"custom.googleapis.com/agent/{metric_type}"
    point = series.points.add()
    point.value.double_value = value
    point.interval.end_time.seconds = int(time.time())
    client.create_time_series(name=project_name, time_series=[series])

# Use in tools
def parse_data_dictionary(data: str) -> Dict[str, Any]:
    start = time.time()
    # ... processing ...
    duration = time.time() - start
    record_metric("parse_duration_seconds", duration)
    return result
```

### 4. Observability Dashboard

Create custom dashboard in Cloud Console:
1. Navigate to **Monitoring > Dashboards**
2. Click **Create Dashboard**
3. Add widgets:
   - **Request Count**: Track usage
   - **Latency**: P50, P95, P99 response times
   - **Error Rate**: 4xx and 5xx errors
   - **Token Usage**: API costs
   - **Memory Usage**: Resource utilization

---

## Troubleshooting

### Common Issues

**Issue 1: Deployment Fails with "Permission Denied"**

```
Error: Permission denied on resource project
```

**Solution**:
```bash
# Check current permissions
gcloud projects get-iam-policy $PROJECT_ID \
    --flatten="bindings[].members" \
    --filter="bindings.members:user:YOUR_EMAIL"

# Add required role
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="user:YOUR_EMAIL" \
    --role="roles/aiplatform.admin"
```

**Issue 2: Agent Times Out**

```
Error: Deadline exceeded
```

**Solution**: Increase timeout in `.agent_engine_config.json`:
```json
{
  "timeout_seconds": 600
}
```

**Issue 3: Out of Memory**

```
Error: Container killed due to memory limit
```

**Solution**: Increase memory allocation:
```json
{
  "resource_limits": {
    "memory": "8Gi"
  }
}
```

**Issue 4: Tool Import Errors**

```
ModuleNotFoundError: No module named 'google.adk'
```

**Solution**: Verify `requirements.txt`:
```txt
google-adk>=1.0.0
google-cloud-aiplatform>=1.38.0
```

**Issue 5: Agent Returns Empty Responses**

**Diagnosis**:
```python
# Check logs
gcloud logging read "resource.type=aiplatform.googleapis.com/Agent" \
    --limit 10 \
    --format json
```

**Common Causes**:
- Tool function errors (check return types)
- LLM rate limiting (add retry logic)
- Invalid tool schemas (verify type hints)

---

## Cost Optimization

### 1. Resource Sizing

**Token Usage Monitoring**:
```python
# Add to tools
def count_tokens(text: str) -> int:
    # Rough estimation: 1 token ≈ 4 characters
    return len(text) // 4

def parse_data_dictionary(data: str) -> Dict[str, Any]:
    tokens_in = count_tokens(data)
    result = # ... processing ...
    tokens_out = count_tokens(json.dumps(result))

    # Log for cost analysis
    logger.info(f"Tokens: {tokens_in} in, {tokens_out} out")
    return result
```

**Estimated Costs** (as of 2025):

| Component | Rate | Monthly Cost (1000 queries) |
|-----------|------|-----------------------------|
| Gemini 2.5 Flash | $0.075 / 1M input tokens | ~$15 |
| Gemini 2.5 Flash | $0.30 / 1M output tokens | ~$30 |
| Agent Engine | $0.05 / hour (0 min instances) | $0 (idle) |
| Agent Engine | $0.05 / hour (1 min instance) | ~$36 |
| Cloud SQL | $0.017 / hour | ~$12 |
| **Total** | | **$57-93/month** |

### 2. Caching Strategies

```python
# Add caching to expensive operations
from functools import lru_cache

@lru_cache(maxsize=100)
def map_to_ontology(variable_name: str, data_type: str) -> Dict[str, Any]:
    # Cached results for repeated queries
    ...
```

### 3. Batch Processing

```python
def parse_data_dictionary_batch(data_list: List[str]) -> List[Dict]:
    """Process multiple dictionaries in one call."""
    return [parse_data_dictionary(data) for data in data_list]
```

### 4. Model Selection

For simpler tasks, use `gemini-2.5-flash-lite` (4x cheaper):

```python
# In agent.py
root_agent = LlmAgent(
    model="gemini-2.5-flash-lite",  # Instead of gemini-2.0-flash-exp
    ...
)
```

---

## Cleanup

### Delete Deployed Agent

```bash
# Using Python SDK
import vertexai
from vertexai import agent_engines

vertexai.init(project=PROJECT_ID, location=REGION)

agents = list(agent_engines.list())
for agent in agents:
    if agent.display_name == "healthcare_documentation_agent":
        agent_engines.delete(resource_name=agent.resource_name, force=True)
        print(f"Deleted agent: {agent.resource_name}")
```

### Delete Container Images

```bash
# List images
gcloud container images list --repository=gcr.io/$PROJECT_ID

# Delete specific image
gcloud container images delete gcr.io/$PROJECT_ID/agent-image:tag --force-delete-tags
```

### Delete Service Account

```bash
gcloud iam service-accounts delete \
    healthcare-agent-sa@$PROJECT_ID.iam.gserviceaccount.com
```

---

## Next Steps

1. **Customize for Your Domain**
   - Add domain-specific ontologies
   - Create custom validation rules
   - Implement organization-specific naming conventions

2. **Add Evaluation Tests**
   ```bash
   adk eval healthcare_documentation_agent \
       tests/integration.evalset.json \
       --config_file_path=tests/test_config.json
   ```

3. **Implement A2A Protocol**
   - Expose as A2A service for cross-organization use
   - Consume external ontology services via A2A

4. **Set Up CI/CD**
   ```yaml
   # .github/workflows/deploy.yml
   name: Deploy Agent
   on:
     push:
       branches: [main]
   jobs:
     deploy:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v2
         - run: adk deploy agent_engine ...
   ```

5. **Configure Production Monitoring**
   - Set up PagerDuty/Slack alerts
   - Create custom dashboards
   - Implement SLO tracking

---

## Resources

- 📚 [ADK Documentation](https://google.github.io/adk-docs/)
- 🚀 [Vertex AI Agent Engine](https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/overview)
- 🏥 [OMOP CDM](https://ohdsi.github.io/CommonDataModel/)
- 🔬 [LOINC Database](https://loinc.org/)
- 🧬 [SNOMED CT](https://www.snomed.org/)
- 💬 [Kaggle Discord](https://discord.com/invite/kaggle)

---

## Support

For issues or questions:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review [Cloud Console logs](https://console.cloud.google.com/logs)
3. Open an issue on [GitHub](https://github.com/dspacks/rdd_orch/issues)
4. Join the [Kaggle Discord](https://discord.com/invite/kaggle) #agents channel

---

**Version:** 2.0
**Last Updated:** 2025-11-22
**Maintainer:** dspacks
**License:** MIT
