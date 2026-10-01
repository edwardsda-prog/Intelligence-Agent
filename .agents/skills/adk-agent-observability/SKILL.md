---
name: adk-agent-observability
description: >-
  Comprehensive guide for instrumenting, exporting, and querying OpenTelemetry GenAI
  semantic conventions in Google Agent Developer Kit (ADK 2.0) agents. Covers Span,
  Trace, Session, and Task execution hierarchies, Cloud Trace, Cloud Logging KQL filters,
  and BigQuery log analytics for production SRE monitoring.
---

# ADK 2.0 OpenTelemetry & GenAI Observability Guide

Production agentic systems require distributed tracing, token accounting, and SRE latency auditing across all operational turns.

---

## 1. OpenTelemetry GenAI Semantic Conventions (openTelemetry.io)

ADK agents follow OpenTelemetry GenAI semantic conventions:

| Attribute Key | Type | Example / Value | Description |
|---|---|---|---|
| `gen_ai.system` | string | `"gcp.vertex_ai"` | GenAI provider/framework identifier |
| `gen_ai.request.model` | string | `"gemini-3.8-flash"` | Target model requested |
| `gen_ai.response.model` | string | `"gemini-3.8-flash"` | Model used for completion |
| `gen_ai.conversation.id` | string | `"session-90412-usr-88"` | Unique multi-turn session ID |
| `gen_ai.usage.prompt_tokens` | int | `1240` | Input token count |
| `gen_ai.usage.completion_tokens` | int | `320` | Output/Thinking token count |
| `gen_ai.prompt` | string | `"Find radar track TRK-901"` | Input prompt text |
| `gen_ai.output.messages` | string (JSON) | `[{"role": "assistant", ...}]` | Model generated response payload |

---

## 2. ADK Distributed Observability Hierarchy

ADK extends standard OpenTelemetry distributed tracing across 4 structural abstractions:

```
[TRACE] End-to-End User Request (Gemini Enterprise -> Agent Gateway -> Reasoning Engine)
  └── [SESSION] Conversation Lifecycle (gen_ai.conversation.id)
        └── [TASK / NODE] Agent Workflow Step (e.g. planner_task, tool_node)
              └── [SPAN] Execution Unit (execute_sql, search_humint_reports, LLM call)
```

---

## 3. Log & Trace Access on Google Cloud Platform

### Cloud Trace Waterfall Analysis
Deploy agents with `--otel_to_cloud` to automatically stream spans to `cloudtrace.googleapis.com`:
```bash
adk deploy agent_engine ./my_agent --otel_to_cloud
```

### Cloud Logging KQL Queries
Query structured logs in Cloud Logging Log Explorer:
```kql
resource.type="aiplatform.googleapis.com/ReasoningEngine"
jsonPayload.attributes."gen_ai.conversation.id"="<SESSION_ID>"
```

### BigQuery Log Sink SRE Analytics
Stream logs to BigQuery for SQL latency (P95/P99) and token burn metrics:
```sql
SELECT 
  jsonPayload.attributes.gen_ai_conversation_id AS session_id,
  AVG(CAST(jsonPayload.attributes.search_output_length AS INT64)) AS avg_payload_bytes,
  SUM(CAST(jsonPayload.attributes.gen_ai_usage_total_tokens AS INT64)) AS total_tokens
FROM `project_id.system_logs.cloudaudit_googleapis_com_activity`
GROUP BY 1;
```

---

## 4. Vertex AI Reasoning Engine Telemetry Collection (Console & Deployment Configuration)

In Google Cloud Console (**Vertex AI > Reasoning Engines / Agent Engines**), the **Telemetry Collection** section exposes two independent checkboxes:

| Console Checkbox | Required Configuration | Default ADK CLI Behavior | Operational Impact |
|---|---|---|---|
| ☑️ **"Enable instrumentation of OpenTelemetry traces, logs and metrics"** | `GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY="true"` (or `--otel_to_cloud`) | Enabled with `--otel_to_cloud` | Emits distributed trace spans to Cloud Trace and request/latency metrics to Cloud Monitoring. |
| ☑️ **"Enable logging of prompt inputs and response outputs"** | `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT="EVENT_ONLY"` (or `"SPAN_AND_EVENT"`) and `ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS="true"` | **Disabled** (`ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS='false'`) | Emits full user prompts, tool arguments, and LLM responses into Cloud Logging events without redaction. |

### Essential Agent Package Configuration (`.agent_engine_config.json` & `.env`)

To prevent the ADK CLI from defaulting `ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS` to `'false'` and to ensure both checkboxes are checked on deployment, place both configuration files in your agent package:

**`my_agent/.agent_engine_config.json`**:
```json
{
  "env_vars": {
    "GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY": "true",
    "OTEL_SEMCONV_STABILITY_OPT_IN": "gen_ai_latest_experimental",
    "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT": "EVENT_ONLY",
    "ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS": "true"
  }
}
```

**`my_agent/.env`**:
```env
GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=true
OTEL_SEMCONV_STABILITY_OPT_IN=gen_ai_latest_experimental
OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=EVENT_ONLY
ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=true
```

And deploy with:
```bash
adk deploy agent_engine ./my_agent --otel_to_cloud
```

