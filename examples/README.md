# Examples - ADK Course Notebooks

This directory contains Jupyter notebooks from the **Agent Development Kit (ADK)** course provided by Google. These notebooks serve as learning materials and reference implementations for working with AI agents using the Google Gemini API.

## Contents

### Day 3: Agent Sessions and Memory
- **day-3a-agent-sessions.ipynb** - Introduction to agent sessions, managing conversation state, and session lifecycle
- **day-3b-agent-memory.ipynb** - Implementing memory systems for agents, context management, and persistence

### Day 4: Observability and Evaluation
- **day-4a-agent-observability.ipynb** - Monitoring agent behavior, logging, debugging, and performance tracking
- **day-4b-agent-evaluation.ipynb** - Testing and evaluating agent performance, quality metrics, and validation

### Day 5: Communication and Deployment
- **day-5a-agent2agent-communication-9a815c.ipynb** - Inter-agent communication patterns, message passing, and coordination
- **day-5b-agent-deployment.ipynb** - Deploying agents to production, best practices, and deployment strategies

## Purpose

These notebooks were used as reference materials during the development of the ADE Healthcare Documentation system. They demonstrate:

- Core concepts of agent development
- Best practices for session management
- Memory and context handling patterns
- Debugging and evaluation techniques
- Multi-agent architectures
- Production deployment strategies

## Relationship to Main Project

The concepts and patterns demonstrated in these notebooks have been applied in the main ADE project:

- **Session Management** → Used in `SessionHistory` table and context management
- **Memory Systems** → Implemented in `ContextManager` and working/long-term memory
- **Observability** → Applied in logging and debugging throughout the codebase
- **Evaluation** → Inspiration for `ValidationAgent` and quality checks
- **Agent Communication** → Used in multi-agent orchestration system
- **Deployment** → Applied in `healthcare_agent_deploy/` for Vertex AI deployment

## Usage

These notebooks are standalone learning materials. To run them:

1. **Set up your environment:**
   ```bash
   pip install google-adk jupyter
   export GOOGLE_API_KEY="your-api-key-here"
   ```

2. **Launch Jupyter:**
   ```bash
   jupyter notebook examples/
   ```

3. **Open and run any notebook** - They are self-contained and include explanations

## Notes

- These notebooks use the `google-adk` package, which is different from `google-generativeai` used in the main project
- The examples demonstrate concepts that can be adapted to various agent development scenarios
- Some notebooks may require additional setup or API keys beyond what's needed for the main ADE project

## Documentation

For more information about the concepts covered in these notebooks, see:
- [AGENTS.md](../docs/AGENTS.md) - Main project agent documentation
- [DATABASE_SCHEMA.md](../docs/DATABASE_SCHEMA.md) - How session and memory are implemented in ADE
- [DAY_NOTEBOOKS_SUMMARY.md](../docs/DAY_NOTEBOOKS_SUMMARY.md) - Detailed notes from these notebooks

## Credits

These notebooks are educational materials from Google's Agent Development Kit course and are provided here for reference purposes.

---

**Last Updated:** 2025-11-22
