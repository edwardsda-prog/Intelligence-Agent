# Observability

## Tri-Tier Telemetry (SRE Hierarchy)
The platform features an advanced telemetry pipeline built around **OpenTelemetry GenAI Semantic Conventions v1.30+**. It categorizes execution into a hierarchy designed for detailed site reliability engineering (SRE):
- **Session** (`session.id`, `user.id`): Groups multi-turn conversations across a user's operational workflow (e.g., `batch_session_1`).
- **Trace** (`trace_id`): Represents the end-to-end execution of a single user prompt from request to completion.
- **Span** (`span_id`, `parent_span_id`): Tracks individual units of work (e.g., LLM inference call, MCP tool call, Model Armor API call).
- **Task** (`gen_ai.task.name`): A background async execution wrapper managing batch evaluation or scheduled routines.

## OpenTelemetry & Cloud Trace
Every LLM call and tool span emits standard OpenTelemetry attributes such as `gen_ai.system="google.adk"`, model name, token usage (prompt, completion, total), tool name, and HTTP status codes.
- **Un-Elided Content Logging**: To guarantee complete auditability, the environment is configured to capture the raw input prompts and output responses without `<elided>` omissions:
  - `GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY="true"`
  - `OTEL_SEMCONV_STABILITY_OPT_IN="gen_ai_latest_experimental"`
  - `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT="EVENT_ONLY"`
  - `ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS="true"`

## Dashboards & Logging
All metrics are exported to Google Cloud Logging and aggregated into two core Cloud Monitoring Dashboards:
1. **Observability Dashboard**: Tracks Agent Execution Latency (via Spans), GenAI Token Usage, Tool Execution Latency (segmented by BigQuery MCP & Discovery Engine), and Session Turn Counts.
2. **Model Armor & OPSEC Compliance Dashboard**: Tracks MGRS Coordinate Redaction Events, Model Armor Intercept Latency, HITL Guardrail Gate Triggers, and NATO Classification Label Compliance.
   - The `apply_model_armor` callback natively emits OpenTelemetry spans and structured logging metric payloads containing `redacted`, `mgrs_count`, and `latency_ms` to populate these metrics.

To facilitate telemetry ingestion and SRE validation, a batch testing script (`prepopulate_dashboards.py`) is used to autonomously feed synthetic queries against the active endpoint and populate the dashboards with live Cloud Logging traces.

For ad-hoc SRE operations, **BigQuery Log Analytics** enables SQL aggregations over the `_AllLogs` table to audit state delta trajectories and token costs per user.

## Business Analytics
The platform captures business adoption and click-through rates (CTR) via Gemini Enterprise **UserEvents**.
- Asynchronous REST streaming to Discovery Engine (`log_discovery_engine_user_event()`) posts interactions to the `userEvents:write` endpoint.
- Operations staff track query volume, pseudo IDs, zero-result rates, and latency distributions inside the Gemini Enterprise Data Store Analytics UI.

## Evaluation & Testing
The system adheres to a highly rigorous 3-Step Evaluation Methodology using the ADK Offline Evaluation Harness:
1. **Map Business KPIs to AI Goals**: Translate executive objectives into measurable criteria.
2. **Author Rubrics with Strong Operational Definitions**: Define binary or sharply bounded criteria emphasizing sensitivity (catching violations) and specificity (avoiding false alarms).
3. **Execute Tiered Evaluation**:
   - *Deterministic Metrics*: Fast hard gates (regex, JSON schemas, SQL match).
   - *Human-Based Evaluation*: Gold-standard baseline calibration.
   - *Model-Based Autoraters*: LLM-as-a-Judge semantic grading, verified by `agreement^k` consistency checks.

Evaluations run against a golden dataset in BigQuery, generating an HTML scorecard analyzing performance across **7 Quality Dimensions**, ensuring reliability before production deployment. ADK evaluates the **trajectory** (e.g. `tool_trajectory_avg_score`) alongside the final response (`response_match_score`), catching "lucky hallucinations" where the agent reaches the right answer without using the mandated tools.
