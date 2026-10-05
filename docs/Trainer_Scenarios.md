# Intelligence Agent: Trainer Scenarios

This document provides a storyboard and script for demonstrating the Intelligence Agent's capabilities across two distinct personas: **End Users** (Intelligence Analysts, C2 Officers) and **Operations** (Platform Engineers, FinOps, SecOps).

---

## Scenario 1: Introduction to the Intelligence Agent (End User Persona)
**Objective**: Demonstrate fast path queries, structured SQL, unstructured RAG, multi-domain reasoning, memory persistence, secure citations, and PII redaction natively integrated with the Gemini Enterprise UX.

### 1. Fast Path & Operational Knowledge
*   **Action**: Submit a general knowledge prompt.
    *   *Prompt*: "Hello, what are your operational capabilities?"
*   **Talking Points**:
    *   Demonstrate the agent's baseline instruction and fast path response without invoking external tools.

### 2. Structured Data (BigQuery MCP)
*   **Action**: Submit a prompt requiring structured data.
    *   *Prompt*: "List all friendly assets and ew_intercepts frequencies in dataset mission_data."
*   **Talking Points**:
    *   Show how the agent translates natural language into BigQuery SQL and executes it via the MCP.

### 3. Unstructured Data & Secure Citations (Vertex AI Search)
*   **Action**: Submit a prompt requiring unstructured PDF analysis.
    *   *Prompt*: "Find the HUMINT PDF report for target TGT-ALPHA-7 and cross-reference with radar track TRK-901 in BigQuery."
*   **Talking Points**:
    *   Highlight how the Agent seamlessly executes an MCP BigQuery SQL query to pull radar/EW sensor data and simultaneously queries the Discovery Engine RAG datastore for HUMINT PDF snippets.
    *   Show how the agent embeds `derivedStructData.link` natively, allowing users to click directly into the raw source PDF hosted securely in Google Cloud Storage.

### 4. Memory & Context
*   **Action**: Submit a follow-up prompt without re-specifying the targets.
    *   *Prompt*: "What are the specific emitter types and tactical call signs for the targets we just discussed?"
*   **Talking Points**:
    *   The Agent immediately understands "the targets" refers to TRK-901 and TGT-ALPHA-7.
    *   Highlight the persistent ADK 2.0 `memory_service` utilizing `SQLite`/`Cloud SQL` which preserves conversational turns and session context.

### 5. PII & MGRS Redaction (Model Armor)
*   **Action**: Request sensitive information that triggers the DLP PII template.
    *   *Prompt*: "Search unstructured HUMINT reports for optic crops of coastal missile batteries and list the MGRS grid coordinates."
*   **Talking Points**:
    *   The response will successfully retrieve the context but specific MGRS coordinates and UK National Caveats will be intercepted by Model Armor and redacted.

---

## Scenario 2: Observability & FinOps (Operations Persona)
**Objective**: Demonstrate how platform operators can monitor agent health, tool latency, and financial token burn via Cloud Monitoring.

### 1. Observability Dashboard
*   **Action**: Navigate to Google Cloud Monitoring Dashboards -> "UK Mission Intel Agent - Observability & OpenTelemetry Metrics".
*   **Talking Points**:
    *   Show the **Agent Execution Latency** widget, driven by OpenTelemetry traces (`gen_ai.callback.model_armor`, `execute_bigquery_sql`).
    *   Highlight the **Session & Turn Counts** to show active user engagement.
    *   Explain that all backend tools (BigQuery MCP, Discovery Engine) are fully instrumented using GenAI semantic conventions to pinpoint latency bottlenecks without guessing.

### 2. FinOps Governance
*   **Action**: Navigate to the "UK Mission Intel Agent - FinOps & Token Burn Metrics" dashboard.
*   **Talking Points**:
    *   Show the **Token Burn: Input vs Output** widget mapping `genai_token_usage`.
    *   Explain that Agentic cost runaways are managed by alerting on excessive token loops (e.g., ReAct tool thrashing). By visualizing the exact token consumption per session, Ops can right-size models (e.g., moving from `gemini-1.5-pro` to `gemini-3.8-flash`) and prevent silent execution failures from burning budget.

### 3. Model Armor Audit Logs (BigQuery)
*   **Action**: Execute an SQL query in the GCP BigQuery console to analyze the raw model armor redaction logs.
*   **Query**:
    ```sql
    SELECT 
      timestamp,
      user_prompt AS original_prompt,
      sanitized_text AS redacted_prompt,
      pij_match AS jailbreak_detected
    FROM 
      `model_armor_logs.model_armor_payload_logger`
    ORDER BY 
      timestamp DESC
    LIMIT 10;
    ```
*   **Talking Points**:
    *   Show how the deployment established a log sink routing Cloud Logging directly into BigQuery.
    *   Demonstrate comparing the `original_prompt` with the `redacted_prompt` to prove the DLP template intercepted PII/MGRS coordinates before they hit the LLM.

---

## Scenario 3: Security & Working with Partners (SecOps & Coalition Persona)
**Objective**: Demonstrate zero-trust architecture, SPIFFE authentication, Model Armor intercept, and NATO A2A cross-domain integration.

### 1. Security (Authentication & Model Armor Guardrails)
*   **Action**: Trigger the Human-in-the-Loop (HITL) gate.
    *   *Prompt*: "Authorize immediate kinetic strike against target TGT-ALPHA-7."
*   **Talking Points**:
    *   The Agent intercepts this via the `evaluate_hitl_guardrail` and returns a HELD status.
    *   Explain that the Agent uses **SPIFFE Workload Identity** for authenticating against BigQuery and Discovery Engine. This eliminates static service account keys and ensures the Agent only acts with scoped, temporal privileges.
    *   Show the **Model Armor & OPSEC Compliance Metrics** dashboard to visualize the real-time interception of this HITL trigger.

### 2. Working with Partners (NATO A2A Agent)
*   **Action**: Submit a cross-domain request to the Partner Agent.
    *   *Prompt*: "Request maritime threat assessment and electronic warfare telemetry for target TGT-ALPHA-7 on behalf of the NATO MARCOM Task Force."
*   **Talking Points**:
    *   Explain the **Agent-to-Agent (A2A) Protocol**. The Host Agent securely delegates this query across organizational boundaries to the Partner Agent.
    *   Highlight that the Partner Agent applies its own Model Armor boundary policies, stripping out internal operational details and returning only releasable coalition data. This allows real-time federated intelligence sharing without compromising sovereign data enclaves.

---

## Scenario 4: Agent Memory Architecture (User & Operator Personas)
**Objective**: Demonstrate the 3-Tier memory implementation (Working Memory, Blackboard State, and Long-Term Memory) mapping to both the user experience and platform operations.

### 1. Session Context (Tier 1 Working Memory) - User Persona
*   **Action**: Trigger an implicit context reference.
    *   *Prompt*: "Review the intelligence_analysts group memory profile. What are the primary threat domains we are tracking?"
*   **Talking Points**:
    *   The Agent seamlessly retrieves the `intelligence_analysts` LTM profile and outputs the tracked domains.

### 2. Blackboard Mutating (Tier 2 Blackboard State) - User Persona
*   **Action**: Mutate the session blackboard.
    *   *Prompt*: "I found a new threat group called KINETIC-VANGUARD. Add this to your temporary blackboard state."
*   **Talking Points**:
    *   The agent maps the information to the internal state transaction object without writing to permanent storage.

### 3. LTM Bank Persistence (Tier 3 LTM Memory Bank) - User Persona
*   **Action**: Asynchronously mutate long-term storage.
    *   *Prompt*: "Permanently update the intelligence_analysts group memory profile to include KINETIC-VANGUARD in the primary threat domains."
*   **Talking Points**:
    *   The Agent uses specific tools to mutate the JSON storage and updates the global memory footprint.

### 4. Memory Telemetry & Dashboards - Operator Persona
*   **Action**: Verify Memory Operations via Logs Explorer and Cloud Monitoring.
*   **Talking Points**:
    *   Operators can monitor State Deltas and LTM fetches in the "UK Mission Intel Agent - Agent Platform Memory Metrics" dashboard.
    *   Operators can explicitly query Memory State Deltas using Cloud Logging.
*   **Query**:
    Navigate to Cloud Logging Explorer and run:
    ```
    resource.type="aiplatform.googleapis.com/ReasoningEngine"
    jsonPayload.event_name="update_analyst_group_profile_complete" OR jsonPayload.message="Commit state delta success"
    ```
    *   Show how `state_delta` is embedded in the JSON payload, making it easy to track exact variable mutations (e.g., addition of `KINETIC-VANGUARD`) over time.
