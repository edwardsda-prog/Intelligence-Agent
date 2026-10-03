# ADK Web User Guide

ADK Web is a built-in FastAPI server that provides a web-based UI for interacting with and debugging your agents locally. This guide covers how to launch the interface, how to use it for A2A testing, and which views are most critical for developers.

## 1. Launching ADK Web

To launch ADK web, run the following command from your terminal:

```bash
adk web --port 8080 --a2a
```

- `--port 8080`: Binds the web UI to port 8080.
- `--a2a`: Enables the Agent-to-Agent endpoint, allowing other external agents to discover and interact with this local instance.

Once running, navigate to `http://localhost:8080` in your web browser.

> [!IMPORTANT]
> **Always run the standalone bash script first:** `./run_local_a2a_agent.sh`
> This script ensures all dependencies are installed and verifies that you have an active Reasoning Engine deployed in your GCP project before launching the ADK Web UI.

## 2. Navigating the Views

ADK Web provides several specialized views. Here is what you should focus on during agent development:

### The Chat Interface (Primary Iteration)
The default view when you launch the UI. It provides a familiar chatbot interface where you can submit prompts to your agent.

**Why use it:** This is the fastest way to iteratively test agent instructions, system prompts, and basic tool execution before deploying to the cloud.

### Traces & Trajectories View
*(Located in the navigation menu)*

This view breaks down the exact sequence of steps (the "Trajectory") the agent took to arrive at its final answer. It exposes the underlying ReAct loop.

**Why use it:** 
- **Latency Debugging:** You can see exactly how many milliseconds each tool call took (e.g. `execute_bigquery_sql` or the `model_armor` callback).
- **Catching "Lucky Hallucinations":** Sometimes an agent provides the factually correct answer by guessing or relying on pre-training data, instead of calling the required RAG or database tools. The Traces view proves whether the agent *actually* executed the required tools, ensuring strict grounding.

### Sessions & Memory View
*(Located in the navigation menu)*

This view allows you to inspect the active `VertexAiSessionService` or local SQLite memory store.

**Why use it:** 
- **Context Verification:** When building stateless agents on Cloud Run, you need to ensure multi-turn conversation context is preserved. This view lets you peek into the agent's memory to verify that entities, targets, and context from previous turns are still available.

## 3. Testing Cross-Domain A2A

If you launched `adk web` with the `--a2a` flag, your local instance is now acting as a host. 

You can test A2A federation by having another agent send requests to your `http://localhost:8080` endpoint. Your local agent will apply its Model Armor boundaries and security constraints just as it would in production, stripping out operational details and returning only releasable data to the requesting agent.
