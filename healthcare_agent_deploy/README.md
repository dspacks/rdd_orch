# Healthcare Documentation Agent - Vertex AI Deployment

**Version:** 2.1 (Full ADE Parity Release)
**Last Updated:** 2025-11-21

This directory contains all files needed to deploy the Healthcare Documentation Agent to Google Cloud's Vertex AI Agent Engine with full parity to the ADE notebook build.

## Directory Structure

```
healthcare_agent_deploy/
├── agent.py                     # Main agent logic with 22 specialized tools (825 lines)
├── requirements.txt             # Python dependencies
├── .env                         # Environment configuration
├── .agent_engine_config.json    # Deployment specifications
└── README.md                    # This file
```

## Quick Start

### 1. Configure Your Project

Edit `.env` and replace `your-project-id` with your actual Google Cloud project ID:

```bash
GOOGLE_CLOUD_PROJECT=my-actual-project-id
```

### 2. Deploy to Vertex AI

```bash
# Set environment variables
export PROJECT_ID="my-actual-project-id"
export REGION="us-central1"

# Deploy using ADK CLI
adk deploy agent_engine \
    --project=$PROJECT_ID \
    --region=$REGION \
    healthcare_agent_deploy \
    --agent_engine_config_file=healthcare_agent_deploy/.agent_engine_config.json
```

### 3. Test the Deployment

```python
import vertexai
from vertexai import agent_engines

vertexai.init(project="my-actual-project-id", location="us-central1")

# Get deployed agent
agents = list(agent_engines.list())
agent = agents[0]

# Test query
response = agent.query(
    message="Parse this data dictionary: patient_id,text,Patient ID",
    user_id="test_user"
)
print(response)
```

## Agent Capabilities

The deployed agent includes **22 specialized tools** across 8 categories:

### What's New in v2.1 ✨

- **Validation Tools** (3 new tools) - Quality assurance for all outputs
- **Batch Processing** (3 new tools) - Handle codebooks with 100+ variables
- **Toon Notation Encoding** - 40-70% token reduction for large datasets
- **Structured Logging** - Cloud Logging integration for observability
- **Performance Tracking** - Timing metrics for all operations
- **Enhanced Instructions** - Production-ready workflow guidance

### Core Healthcare Documentation (3 tools)
- `parse_data_dictionary` - Parse CSV/JSON data dictionaries
- `map_to_ontology` - Map to OMOP, LOINC, SNOMED codes
- `generate_documentation` - Create human-readable documentation

### Design Improvement (2 tools)
- `improve_document_design` - Enhance structure and readability
- `analyze_design_patterns` - Identify design inconsistencies

### Data Conventions (2 tools)
- `analyze_variable_conventions` - Detect naming patterns
- `generate_conventions_glossary` - Create standards documentation

### Version Control (4 tools)
- `create_version` - Track changes with semantic versioning
- `get_version_history` - View complete version history
- `rollback_version` - Revert to previous versions
- `compare_versions` - Diff between versions

### Higher-Level Documentation (4 tools)
- `identify_instruments` - Auto-detect measurement scales
- `document_instrument` - Create instrument-level documentation
- `document_segment` - Document logical variable groupings
- `generate_codebook_overview` - Comprehensive codebook summary

### Memory (2 tools)
- `save_to_memory` - Store findings across sessions
- `retrieve_from_memory` - Recall previous learnings

### Validation ✨ NEW (3 tools)
- `validate_documentation_quality` - Check documentation completeness and quality
- `validate_variable_data` - Validate variable structure and required fields
- `validate_batch_results` - Verify batch processing results

### Batch Processing ✨ NEW (3 tools)
- `process_large_codebook` - Split large codebooks into manageable batches
- `get_batch_progress` - Track processing progress
- `mark_batch_complete` - Mark batches as completed

## Configuration Details

### Resource Limits

The default configuration in `.agent_engine_config.json`:

- **Min Instances:** 0 (scales to zero when idle)
- **Max Instances:** 3 (handles up to 3 concurrent requests)
- **CPU:** 2 vCPUs per instance
- **Memory:** 4Gi per instance
- **Timeout:** 300 seconds (5 minutes)

Adjust these based on your workload:

```json
{
  "min_instances": 1,        // Set to 1+ for production (reduces cold starts)
  "max_instances": 10,       // Increase for high traffic
  "resource_limits": {
    "cpu": "4",             // More CPU for faster processing
    "memory": "8Gi"         // More memory for large codebooks
  },
  "timeout_seconds": 600    // Increase for complex processing
}
```

### Model Selection

The agent uses `gemini-2.5-flash-lite` for cost-efficiency. To use a more powerful model, edit `agent.py`:

```python
root_agent = LlmAgent(
    model="gemini-2.0-flash-exp",  # More capable but 4x more expensive
    # ... rest of configuration
)
```

## Cost Estimation

Based on typical usage (1000 queries/month):

| Component | Monthly Cost |
|-----------|--------------|
| Gemini 2.5 Flash (input) | ~$15 |
| Gemini 2.5 Flash (output) | ~$30 |
| Agent Engine (min_instances=0) | $0 (idle) |
| Agent Engine (min_instances=1) | ~$36 |
| **Total** | **$45-81/month** |

## Testing Locally Before Deployment

You can test the agent logic locally before deploying:

```python
# Test parse_data_dictionary
from agent import parse_data_dictionary, validate_variable_data

test_data = """Variable Name,Field Type,Field Label
patient_id,text,Patient ID
age,integer,Age"""

result = parse_data_dictionary(test_data)
print(result)

# Test validation (NEW in v2.1)
for var in result['variables']:
    validation = validate_variable_data(var)
    print(f"Validation for {var.get('Variable Name')}: Score {validation['overall_score']}")
```

## Production Considerations

Before deploying to production:

1. **Security:**
   - Use service accounts instead of user credentials
   - Enable VPC Service Controls for HIPAA compliance
   - Configure Cloud Armor for DDoS protection

2. **Monitoring:**
   - Set up Cloud Monitoring alerts
   - Enable Cloud Logging
   - Track token usage and costs

3. **Scaling:**
   - Set appropriate min/max instances
   - Monitor cold start times
   - Use connection pooling for databases

4. **Compliance:**
   - Ensure HIPAA compliance for PHI
   - Implement audit logging
   - Configure data retention policies

## Troubleshooting

### Deployment Fails

```bash
# Check IAM permissions
gcloud projects get-iam-policy $PROJECT_ID

# Enable required APIs
gcloud services enable aiplatform.googleapis.com
```

### Agent Times Out

Increase `timeout_seconds` in `.agent_engine_config.json`:

```json
{
  "timeout_seconds": 600
}
```

### Out of Memory

Increase memory allocation:

```json
{
  "resource_limits": {
    "memory": "8Gi"
  }
}
```

## Cleanup

To delete the deployed agent:

```python
import vertexai
from vertexai import agent_engines

vertexai.init(project=PROJECT_ID, location=REGION)

agents = list(agent_engines.list())
for agent in agents:
    if agent.display_name == "healthcare_documentation_agent":
        agent_engines.delete(resource_name=agent.resource_name, force=True)
```

## Version History

### v2.1 (2025-11-21) - Full ADE Parity Release ✨
- Added 6 new tools (3 validation + 3 batch processing)
- Implemented Toon Notation for 40-70% token reduction
- Added structured logging and observability
- Enhanced agent instructions for production workflows
- **Total Tools: 22** (up from 16 in v2.0)
- **Feature Parity: ~85%** with ADE notebook

### v2.0 (2025-11-19) - Initial Extended Capabilities
- 16 tools across 6 categories
- Core healthcare documentation features

## Documentation

For complete deployment guide, see: [VERTEX_AI_DEPLOYMENT.md](../VERTEX_AI_DEPLOYMENT.md)

For ADK documentation, visit: https://google.github.io/adk-docs/

## Support

- GitHub Issues: https://github.com/dspacks/rdd_orch/issues
- Kaggle Discord: https://discord.com/invite/kaggle (#agents channel)

## License

MIT License - See [LICENSE](../LICENSE) for details
