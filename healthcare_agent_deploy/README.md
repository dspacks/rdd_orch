# Healthcare Documentation Agent - Vertex AI Deployment

This directory contains all files needed to deploy the Healthcare Documentation Agent to Google Cloud's Vertex AI Agent Engine.

## Directory Structure

```
healthcare_agent_deploy/
├── agent.py                     # Main agent logic with 16 specialized tools
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

The deployed agent includes **16 specialized tools** across 6 categories:

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
from agent import parse_data_dictionary

test_data = """Variable Name,Field Type,Field Label
patient_id,text,Patient ID
age,integer,Age"""

result = parse_data_dictionary(test_data)
print(result)
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

## Documentation

For complete deployment guide, see: [VERTEX_AI_DEPLOYMENT.md](../VERTEX_AI_DEPLOYMENT.md)

For ADK documentation, visit: https://google.github.io/adk-docs/

## Support

- GitHub Issues: https://github.com/dspacks/rdd_orch/issues
- Kaggle Discord: https://discord.com/invite/kaggle (#agents channel)

## License

MIT License - See [LICENSE](../LICENSE) for details
