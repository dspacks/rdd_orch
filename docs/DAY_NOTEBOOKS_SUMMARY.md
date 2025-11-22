# ADK (Agent Development Kit) Course Summary

This document summarizes the key concepts, code snippets, and implementation patterns from the Kaggle 5-day AI Agents course using Google's Agent Development Kit (ADK).

---

## Day 3a: Session Management

### Overview
Sessions provide **short-term memory** for agents, maintaining conversation context within a single interaction thread.

### Key Concepts
- **Session**: Container for conversations with chronological events
- **Events**: Building blocks of conversation (user input, agent responses, tool calls)
- **State**: Key-value storage available to all sub-agents and tools
- **SessionService**: Storage layer for session data
- **Runner**: Orchestration layer managing information flow

### Core Implementation

```python
from google.adk.agents import Agent, LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.sessions import InMemorySessionService, DatabaseSessionService
from google.adk.runners import Runner
from google.genai import types

# Retry configuration for API resilience
retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],
)

# Create agent
root_agent = Agent(
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    name="text_chat_bot",
    description="A text chatbot",
)

# Session service options
session_service = InMemorySessionService()  # For testing (non-persistent)
# OR
session_service = DatabaseSessionService(db_url="sqlite:///my_agent_data.db")  # Persistent

# Create runner
runner = Runner(agent=root_agent, app_name="app_name", session_service=session_service)
```

### Running Sessions

```python
async def run_session(runner_instance, user_queries, session_name="default"):
    app_name = runner_instance.app_name

    try:
        session = await session_service.create_session(
            app_name=app_name, user_id=USER_ID, session_id=session_name
        )
    except:
        session = await session_service.get_session(
            app_name=app_name, user_id=USER_ID, session_id=session_name
        )

    for query in user_queries:
        query_content = types.Content(role="user", parts=[types.Part(text=query)])
        async for event in runner_instance.run_async(
            user_id=USER_ID, session_id=session.id, new_message=query_content
        ):
            if event.content and event.content.parts:
                print(event.content.parts[0].text)
```

### Context Compaction

```python
from google.adk.apps.app import App, EventsCompactionConfig

# Auto-summarize conversation history to reduce context size
app = App(
    name="research_app",
    root_agent=chatbot_agent,
    events_compaction_config=EventsCompactionConfig(
        compaction_interval=3,  # Trigger after every 3 invocations
        overlap_size=1,  # Keep 1 previous turn for context
    ),
)

runner = Runner(app=app, session_service=session_service)
```

### Session State Management

```python
from google.adk.tools.tool_context import ToolContext

def save_userinfo(tool_context: ToolContext, user_name: str, country: str) -> dict:
    """Store data in session state using prefixes for organization."""
    tool_context.state["user:name"] = user_name
    tool_context.state["user:country"] = country
    return {"status": "success"}

def retrieve_userinfo(tool_context: ToolContext) -> dict:
    """Retrieve data from session state."""
    user_name = tool_context.state.get("user:name", "Not found")
    country = tool_context.state.get("user:country", "Not found")
    return {"user_name": user_name, "country": country}

# Use in agent
agent = LlmAgent(
    model=Gemini(model="gemini-2.5-flash-lite"),
    name="stateful_bot",
    tools=[save_userinfo, retrieve_userinfo],
)
```

---

## Day 3b: Memory Management

### Overview
Memory provides **long-term knowledge storage** across multiple conversations, enabling agents to recall information from past sessions.

### Key Concepts
- **Session** = Short-term memory (single conversation)
- **Memory** = Long-term knowledge (across conversations)
- Cross-conversation recall
- Semantic search capability (with managed services)
- LLM-powered consolidation

### Core Implementation

```python
from google.adk.memory import InMemoryMemoryService
from google.adk.tools import load_memory, preload_memory

# Initialize memory service
memory_service = InMemoryMemoryService()

# Create runner with BOTH session and memory services
runner = Runner(
    agent=user_agent,
    app_name="MemoryDemoApp",
    session_service=session_service,
    memory_service=memory_service,  # Enable memory!
)
```

### Memory Retrieval Tools

```python
# Reactive: Agent decides when to search
agent_reactive = LlmAgent(
    model=Gemini(model="gemini-2.5-flash-lite"),
    name="ReactiveAgent",
    instruction="Use load_memory tool if you need to recall past conversations.",
    tools=[load_memory],
)

# Proactive: Automatically loads memory before every turn
agent_proactive = LlmAgent(
    model=Gemini(model="gemini-2.5-flash-lite"),
    name="ProactiveAgent",
    tools=[preload_memory],
)
```

### Manual Memory Operations

```python
# Store session in memory
session = await session_service.get_session(app_name, user_id, session_id)
await memory_service.add_session_to_memory(session)

# Search memory
search_response = await memory_service.search_memory(
    app_name=APP_NAME,
    user_id=USER_ID,
    query="What is the user's favorite color?"
)
for memory in search_response.memories:
    print(memory.content.parts[0].text)
```

### Automated Memory Storage with Callbacks

```python
async def auto_save_to_memory(callback_context):
    """Automatically save session to memory after each agent turn."""
    await callback_context._invocation_context.memory_service.add_session_to_memory(
        callback_context._invocation_context.session
    )

auto_memory_agent = LlmAgent(
    model=Gemini(model="gemini-2.5-flash-lite"),
    name="AutoMemoryAgent",
    tools=[preload_memory],
    after_agent_callback=auto_save_to_memory,  # Auto-save after each turn
)
```

---

## Day 4a: Agent Observability

### Overview
Observability provides visibility into agent decision-making through logs, traces, and metrics.

### Three Pillars
1. **Logs**: Record of single events (what happened)
2. **Traces**: Connected sequence showing why results occurred
3. **Metrics**: Summary numbers (how well agent performs)

### ADK Web UI with Debug Logging

```bash
# Start ADK web UI with debug logging
adk web --log_level DEBUG
```

### Creating Tools with Proper Type Hints

```python
from typing import List

# CORRECT: Use proper type hints
def count_papers(papers: List[str]):
    """Count papers in a list."""
    return len(papers)

# WRONG: String type causes issues
def count_papers_wrong(papers: str):
    """This will cause bugs!"""
    return len(papers)  # Returns character count, not item count
```

### Using LoggingPlugin

```python
from google.adk.runners import InMemoryRunner
from google.adk.plugins.logging_plugin import LoggingPlugin

runner = InMemoryRunner(
    agent=research_agent,
    plugins=[LoggingPlugin()],  # Auto-capture all agent activity
)

# Run with logging
response = await runner.run_debug("Find papers on quantum computing")
```

### Custom Plugins

```python
from google.adk.plugins.base_plugin import BasePlugin
from google.adk.agents.callback_context import CallbackContext

class CountInvocationPlugin(BasePlugin):
    def __init__(self):
        super().__init__(name="count_invocation")
        self.agent_count = 0
        self.llm_request_count = 0

    async def before_agent_callback(self, *, agent, callback_context: CallbackContext):
        self.agent_count += 1
        logging.info(f"Agent run count: {self.agent_count}")

    async def before_model_callback(self, *, callback_context: CallbackContext, llm_request):
        self.llm_request_count += 1
        logging.info(f"LLM request count: {self.llm_request_count}")
```

---

## Day 4b: Agent Evaluation

### Overview
Systematic testing to ensure agents perform correctly across various scenarios. Evaluation is **proactive** (catches issues early) vs observability which is **reactive** (diagnoses after issues occur).

### Key Metrics
- **Response Match Score**: Text similarity between expected and actual response (0-1)
- **Tool Trajectory Score**: Whether agent used correct tools with correct parameters (0-1)

### Evaluation Configuration

```python
# test_config.json
{
    "criteria": {
        "tool_trajectory_avg_score": 1.0,  # Perfect tool usage
        "response_match_score": 0.8        # 80% text similarity
    }
}
```

### Creating Test Cases (evalset.json)

```python
test_cases = {
    "eval_set_id": "home_automation_suite",
    "eval_cases": [
        {
            "eval_id": "living_room_light_on",
            "conversation": [
                {
                    "user_content": {
                        "parts": [{"text": "Turn on the floor lamp in the living room"}]
                    },
                    "final_response": {
                        "parts": [{"text": "Successfully set the floor lamp to on."}]
                    },
                    "intermediate_data": {
                        "tool_uses": [
                            {
                                "name": "set_device_status",
                                "args": {
                                    "location": "living room",
                                    "device_id": "floor lamp",
                                    "status": "ON",
                                },
                            }
                        ]
                    },
                }
            ],
        },
    ],
}

# Save to file
with open("agent/integration.evalset.json", "w") as f:
    json.dump(test_cases, f, indent=2)
```

### Running CLI Evaluation

```bash
adk eval home_automation_agent \
    home_automation_agent/integration.evalset.json \
    --config_file_path=home_automation_agent/test_config.json \
    --print_detailed_results
```

### ADK Web UI Evaluation
1. Select agent in dropdown
2. Have conversation
3. Navigate to **Eval** tab
4. Click **Create Evaluation set**
5. Add current session as test case
6. Run evaluation to compare

---

## Day 5a: Agent2Agent (A2A) Communication

### Overview
Standard protocol for agents to communicate across networks, frameworks, and organizations.

### Key Concepts
- **Agent Card**: JSON describing agent capabilities (name, skills, URL)
- **A2A Protocol**: Standardized HTTP communication between agents
- **RemoteA2aAgent**: Client-side proxy for consuming remote agents
- **to_a2a()**: Expose ADK agent as A2A service

### Use Cases
- Cross-framework integration
- Cross-language communication
- Cross-organization boundaries

### Exposing an Agent via A2A

```python
from google.adk.a2a.utils.agent_to_a2a import to_a2a

# Create agent
product_catalog_agent = LlmAgent(
    model=Gemini(model="gemini-2.5-flash-lite"),
    name="product_catalog_agent",
    tools=[get_product_info],
)

# Convert to A2A app
a2a_app = to_a2a(product_catalog_agent, port=8001)
# Auto-generates agent card at /.well-known/agent-card.json
```

### Starting A2A Server

```python
# Save agent to file, then run with uvicorn
server_process = subprocess.Popen([
    "uvicorn",
    "product_catalog_server:app",
    "--host", "localhost",
    "--port", "8001",
])
```

### Consuming Remote Agents

```python
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent, AGENT_CARD_WELL_KNOWN_PATH

# Create proxy for remote agent
remote_agent = RemoteA2aAgent(
    name="product_catalog_agent",
    description="Remote product catalog from external vendor",
    agent_card=f"http://localhost:8001{AGENT_CARD_WELL_KNOWN_PATH}",
)

# Use as sub-agent
customer_support_agent = LlmAgent(
    model=Gemini(model="gemini-2.5-flash-lite"),
    name="customer_support_agent",
    instruction="Use product_catalog_agent to look up product information.",
    sub_agents=[remote_agent],  # Treat remote agent as local sub-agent
)
```

### Testing A2A Communication

```python
async def test_a2a(query: str):
    session_service = InMemorySessionService()
    session = await session_service.create_session(
        app_name="app", user_id="user", session_id="session"
    )

    runner = Runner(
        agent=customer_support_agent,
        app_name="app",
        session_service=session_service
    )

    message = types.Content(parts=[types.Part(text=query)])

    async for event in runner.run_async(
        user_id="user", session_id="session", new_message=message
    ):
        if event.is_final_response() and event.content:
            for part in event.content.parts:
                print(part.text)

await test_a2a("Tell me about iPhone 15 Pro")
```

---

## Day 5b: Agent Deployment to Vertex AI Agent Engine

### Overview
Deploy agents to production using Vertex AI Agent Engine for fully managed, auto-scaling infrastructure.

### Project Structure

```
sample_agent/
├── agent.py                     # Agent logic
├── requirements.txt             # Dependencies
├── .env                         # Configuration
└── .agent_engine_config.json    # Deployment specs
```

### Requirements File

```txt
google-adk
opentelemetry-instrumentation-google-genai
```

### Environment Configuration (.env)

```bash
GOOGLE_CLOUD_LOCATION="global"
GOOGLE_GENAI_USE_VERTEXAI=1
```

### Agent Code for Deployment

```python
# agent.py
from google.adk.agents import Agent
import vertexai
import os

vertexai.init(
    project=os.environ["GOOGLE_CLOUD_PROJECT"],
    location=os.environ["GOOGLE_CLOUD_LOCATION"],
)

def get_weather(city: str) -> dict:
    """Tool for getting weather information."""
    weather_data = {
        "san francisco": {"status": "success", "report": "Sunny, 72°F"},
        "new york": {"status": "success", "report": "Cloudy, 65°F"},
    }
    return weather_data.get(city.lower(), {"status": "error", "error_message": "City not found"})

root_agent = Agent(
    name="weather_assistant",
    model="gemini-2.5-flash-lite",
    description="Weather assistant",
    instruction="Use get_weather tool for weather queries.",
    tools=[get_weather]
)
```

### Deployment Configuration

```json
{
    "min_instances": 0,
    "max_instances": 1,
    "resource_limits": {"cpu": "1", "memory": "1Gi"}
}
```

### Deploy Using ADK CLI

```bash
adk deploy agent_engine \
    --project=$PROJECT_ID \
    --region=$REGION \
    sample_agent \
    --agent_engine_config_file=sample_agent/.agent_engine_config.json
```

### Testing Deployed Agent

```python
import vertexai
from vertexai import agent_engines

vertexai.init(project=PROJECT_ID, location=deployed_region)

# Retrieve deployed agent
agents_list = list(agent_engines.list())
remote_agent = agents_list[0]

# Query the agent
async for item in remote_agent.async_stream_query(
    message="What is the weather in Tokyo?",
    user_id="user_42",
):
    print(item)
```

### Cleanup

```python
agent_engines.delete(resource_name=remote_agent.resource_name, force=True)
```

---

## Healthcare ADE Agent Deployment (Extended Implementation)

### Overview

The Healthcare Data Documentation Agent in this repository extends the basic deployment pattern with **16 specialized tools** across 6 categories for comprehensive healthcare data documentation.

### Project Structure

```
healthcare_agent_deploy/
├── agent.py                     # Agent with 16 specialized tools
├── requirements.txt             # Python dependencies
├── .env                         # Environment configuration
├── .agent_engine_config.json    # Deployment specifications (2 CPU, 4Gi RAM)
└── README.md                    # Deployment instructions
```

### Extended Agent Capabilities

The deployed agent includes:

**Core Healthcare Documentation (3 tools)**
- `parse_data_dictionary` - Parse CSV/JSON data dictionaries
- `map_to_ontology` - Map to OMOP, LOINC, SNOMED codes
- `generate_documentation` - Create human-readable docs

**Design Improvement (2 tools)**
- `improve_document_design` - Enhance structure and readability with quality scores
- `analyze_design_patterns` - Identify design inconsistencies

**Data Conventions (2 tools)**
- `analyze_variable_conventions` - Detect naming patterns (snake_case, camelCase, etc.)
- `generate_conventions_glossary` - Create standards documentation

**Version Control (4 tools)**
- `create_version` - Track changes with semantic versioning
- `get_version_history` - View complete version history
- `rollback_version` - Revert to previous versions
- `compare_versions` - Diff between versions

**Higher-Level Documentation (4 tools)**
- `identify_instruments` - Auto-detect measurement scales (e.g., PHQ-9, GAD-7)
- `document_instrument` - Create instrument-level documentation
- `document_segment` - Document logical variable groupings
- `generate_codebook_overview` - Comprehensive codebook summary

**Memory (2 tools)**
- `save_to_memory` - Store findings across sessions
- `retrieve_from_memory` - Recall previous learnings

### Deployment Configuration

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

**Note:** 4Gi memory allocation supports processing large codebooks (1000+ variables)

### Deploy Healthcare Agent

```bash
# From the repository root
export PROJECT_ID="your-project-id"
export REGION="us-central1"

adk deploy agent_engine \
    --project=$PROJECT_ID \
    --region=$REGION \
    healthcare_agent_deploy \
    --agent_engine_config_file=healthcare_agent_deploy/.agent_engine_config.json
```

### Testing with Healthcare Data

```python
import vertexai
from vertexai import agent_engines

vertexai.init(project=PROJECT_ID, location=REGION)

agents_list = list(agent_engines.list())
healthcare_agent = agents_list[0]

# Test with sample healthcare data dictionary
test_data = """Variable Name,Field Type,Field Label,Notes
patient_id,text,Patient ID,Unique identifier
age,integer,Age (years),Age at enrollment
bp_systolic,integer,Systolic BP,mmHg
hba1c,decimal,HbA1c (%),Glycemic control marker"""

response = healthcare_agent.query(
    message=f"Parse this data dictionary, map to ontologies, and generate comprehensive documentation:\n\n{test_data}",
    user_id="test_user"
)
print(response)
```

### Extended Workflow Example

The agent can handle complex multi-step workflows:

```python
# Step 1: Parse and analyze conventions
response1 = healthcare_agent.query(
    message="Analyze variable naming conventions in this dataset",
    user_id="user_001"
)

# Step 2: Identify instruments
response2 = healthcare_agent.query(
    message="Identify any measurement instruments (PHQ-9, GAD-7, etc.) based on variable prefixes",
    user_id="user_001"
)

# Step 3: Create version-controlled documentation
response3 = healthcare_agent.query(
    message="Generate documentation for patient_id and create version 1.0.0",
    user_id="user_001"
)

# Step 4: Update and track changes
response4 = healthcare_agent.query(
    message="Update patient_id documentation with new notes and create a new version",
    user_id="user_001"
)

# Step 5: Compare versions
response5 = healthcare_agent.query(
    message="Compare version 1.0.0 and 1.0.1 of patient_id documentation",
    user_id="user_001"
)
```

### Production Considerations for Healthcare

1. **HIPAA Compliance**
   - Use VPC Service Controls
   - Enable audit logging
   - Configure data retention policies

2. **PHI Detection**
   - Add PHI pattern detection before processing
   - Reject data containing SSN, MRN, or other identifiers

3. **Ontology Updates**
   - Regularly update OMOP/LOINC/SNOMED mappings
   - Version control ontology dictionaries

4. **Cost Optimization**
   - Use caching for repeated ontology lookups
   - Set `min_instances: 0` for development
   - Monitor token usage (typical: 500-1000 tokens per variable)

### Documentation

For complete deployment guide with troubleshooting, monitoring, and cost optimization, see:
- [VERTEX_AI_DEPLOYMENT.md](../VERTEX_AI_DEPLOYMENT.md)
- [healthcare_agent_deploy/README.md](../healthcare_agent_deploy/README.md)

---

## Key Patterns Summary

### 1. Agent Creation Pattern
```python
agent = LlmAgent(
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    name="agent_name",
    description="Agent description",
    instruction="System prompt with behavior guidelines",
    tools=[tool1, tool2],
    sub_agents=[sub_agent1],
    after_agent_callback=callback_function,
)
```

### 2. Runner Pattern
```python
runner = Runner(
    agent=root_agent,           # OR app=app_with_config
    app_name="app_name",
    session_service=session_service,
    memory_service=memory_service,  # Optional
)
```

### 3. Tool Pattern
```python
def tool_name(param1: Type1, param2: Type2) -> dict:
    """
    Tool description for agent to understand when to use it.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Dictionary with results
    """
    # Implementation
    return {"status": "success", "data": result}
```

### 4. Callback Pattern
```python
async def callback_function(callback_context):
    """Execute custom logic at specific points in agent lifecycle."""
    # Access session, memory, etc. via callback_context
    pass
```

### 5. Async Streaming Pattern
```python
async for event in runner.run_async(user_id, session_id, new_message):
    if event.is_final_response() and event.content:
        for part in event.content.parts:
            print(part.text)
```

---

## Production Considerations

1. **Use persistent storage** (DatabaseSessionService) instead of InMemorySessionService
2. **Configure retry options** for API resilience
3. **Implement proper error handling** in tools
4. **Use context compaction** for long conversations
5. **Enable observability** with LoggingPlugin or custom plugins
6. **Create comprehensive evaluation test cases**
7. **Consider A2A for microservices architecture**
8. **Clean up resources** after deployment testing to avoid costs
9. **Use Vertex AI Memory Bank** for cross-session knowledge
10. **Monitor deployed agents** via Google Cloud Console

---

## Resources

- [ADK Documentation](https://google.github.io/adk-docs/)
- [A2A Protocol](https://a2a-protocol.org/)
- [Vertex AI Agent Engine](https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/overview)
- [Kaggle Discord](https://discord.com/invite/kaggle)
