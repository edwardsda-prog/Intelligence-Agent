# Feature Specification: Mission Intelligence Ecosystem

**Feature Branch**: `main`
**Created**: 2026-09-26
**Status**: Approved / Demonstrator Baseline
**Input**: Multi-domain Command and Control (MDC2) intelligence decision-support platform for the UK Ministry of Defence (MOD) and Defence Industrial Base (DIB), synthesizing structured telemetry and unstructured HUMINT field reports using Agentic AI (ADK 2.0, Gemini 3.8 Flash, Vertex AI Reasoning Engine, Model Context Protocol, and Agent-to-Agent Federation).
**Security Classification**: Demonstrator
**Runtime Environment**: Python 3.11+

---

## 1. Quick Reference & Core Areas (Agent Execution Context)

### 1.1. Executable Commands

```bash
# Bootstrap & Environment Provisioning
./infrastructure/setup.sh

# Run Complete End-to-End Automated Test Suite (Mock / Hermetic Mode)
./src/tests/test_e2e.sh --mock

# Run Live Google Cloud Platform Test Suite
./src/tests/test_e2e.sh

# Execute Common Module Unit Tests Directly
python3 -m unittest discover -s src/tests -p 'test_*.py' -v

# Run Offline Evaluation Benchmark (7 Quality Dimensions)
python3 src/tests/run_offline_evaluation.py --mock

# Validate Shell Scripts Syntax
bash -n infrastructure/setup.sh && bash -n src/tests/test_e2e.sh
```

### 1.2. Testing & Conformance
* **Test Runner:** Python `unittest` harness integrated via `test_e2e.sh`.
* **Test Suites:**
  * Unit tests reside in `src/tests/` (`test_data.py`, `test_resilience.py`, `test_telemetry.py`, `test_hitl.py`, `test_caching.py`, `test_grounding.py`, `test_performance.py`, `test_opsec.py`, `test_rag.py`).
  * Conformance tests evaluate all scenarios sequentially, validating Unit Tests, Analytical SQL Queries, and Interactive Prompts.

### 1.3. Project Structure & File Layout
* `src/agent/`: Agent Developer Kit (ADK 2.0) agent runtime, ReAct cognitive loops, and sub-50ms Fast-Path intercepts.
* `src/a2a_mesh/`: Secure Agent-to-Agent (A2A) protocol federation, Agent Gateway routing, and NATO caveat boundary enforcement.
* `src/common/`: Shared resilient libraries (`resilience.py`, `telemetry.py`, `caching.py`, `hitl.py`).
* `src/tests/`: End-to-end verification and unit test suite.
* `infrastructure/`: Setup scripts, deploy scripts, and schema files.
* `data/`: Structured SQL and Unstructured HUMINT data used for population and testing.
* `docs/`: Reference documentation, architecture plans, and prompt guides.

### 1.4. Code Style & Technical Conventions
* **Language & Typing:** Strictly Python 3.11+ using explicit type annotations.
* **Data Validation:** Pydantic v2 schemas and dataclasses for structured parameters and tool contracts.
* **Docstrings:** Google-style docstrings with explicit parameter and return specifications.
* **Exception Handling:** Structured domain exceptions; no bare `except:` blocks; explicit retry handling via exponential backoff with jitter.

### 1.5. Git Workflow
* **Branch Strategy:** Work occurs on `main` for release baselines; feature topics branch off `main`.
* **Commit Conventions:** Follow Conventional Commits format.
* **Pre-Commit Gate:** Must execute `./src/tests/test_e2e.sh --mock` and verify all tests pass with 0 regressions before committing.

### 1.6. Three-Tier Boundaries (Agent Rules of Engagement)

* **✅ Always Do:**
  * Run `./src/tests/test_e2e.sh --mock` before proposing git commits.
  * Maintain security classification strictly as `Demonstrator` (or `Demonstrator // REL TO NATO`).
  * Source all cloud environment parameters dynamically (`PROJECT_ID`, `LOCATION`, `STAGING_BUCKET`).
  * Route Gemini 3.8 Flash (`gemini-3.8-flash`) Context Caching to `location="global"`.
  * Ensure dual telemetry (OpenTelemetry spans and full prompt/response message logging) is configured.

* **⚠️ Ask First:**
  * Altering BigQuery table schemas or column names in `mission_data`.
  * Introducing new external Python dependencies.
  * Changing circuit breaker failure thresholds or cooldown durations in production configs.

* **🚫 Never Do:**
  * Never commit API keys, service account JSON secrets, or plaintext credentials.
  * Never output or leak unredacted raw MGRS tactical coordinates across external or coalition boundaries.
  * Never bypass or execute kinetic strikes or offensive cyber countermeasures without explicit cryptographic `AUTH_<HASH>` validation.

---

## 2. User Scenarios & Testing

### User Story 1 - Multi-Domain Sensor Telemetry Fusion (Priority: P1 - MVP)
As a UK Ministry of Defence Joint Command Staff Analyst, I want to query an integrated Common Operational Picture (COP) across radar, electronic warfare, satellite reconnaissance, and cyber intelligence, so that I can identify and correlate incoming hostile threats in seconds rather than hours.

### User Story 2 - Spec-Driven ReAct Reasoning & Autonomous Error Recovery (Priority: P2)
As a Tactical Watch Officer, I want an autonomous agent that plans, executes multi-hop SQL tool calls, and recovers from database schema exceptions, so that mission queries succeed continuously without crashing during high-tempo operations. Includes Tier 1 Fast-Path intercepts for <50ms response to routine queries.

### User Story 3 - Decoupled Tool Sandboxing & Telemetry Auditing (Priority: P3)
As a Defence Enterprise Cloud Architect, I want database tools isolated on serverless Cloud Run microservices via the Model Context Protocol (MCP) with full OpenTelemetry and audit logging, so that agent compute is decoupled from data storage and all reasoning steps are verifiably compliant with defense audit standards.

### User Story 4 - DevSecOps OPSEC Sanitization & Human-in-the-Loop Gateway (Priority: P4)
As a UK MOD Operational Security (OPSEC) Officer, I want automated redaction of sensitive tactical coordinates (MGRS) using Cloud DLP and Model Armor, and mandatory cryptographic authorization for kinetic actions (`AUTH_<HASH>`).

### User Story 5 - Multimodal RAG with Page Citations & Global Context Caching (Priority: P5)
As an Intelligence Watch Officer, I want to query unstructured multimodal HUMINT PDF dossiers with exact page-level citations alongside high-performance context caching (>32k tokens, 60m TTL, `location="global"`).

### User Story 6 - Scientific Harness Evaluation across 7 Quality Dimensions (Priority: P6)
As a Defence AI Evaluation Engineer, I want automated offline evaluation benchmarking the agent against a golden intelligence dataset across 7 Quality Dimensions (Groundedness, Factual Accuracy, Instruction Following, Safety & OPSEC, Latency & Cost Efficiency, Actionability, Digestibility), requiring an aggregate score of $\ge 4.5/5.0$.

### User Story 7 - Secure Coalition Agent-to-Agent (A2A) Federation (Priority: P7)
As a NATO Coalition Task Force Commander, I want allied partner agents to query the UK Host Agent via the Agent-to-Agent (A2A) protocol over a secure Agent Gateway, enforcing `Demonstrator // REL TO NATO` classification caveats and blocking kinetic actions.

---

## 3. Requirements

### 3.1. Functional Requirements
* **FR-001**: System MUST ingest and maintain structured telemetry across six distinct operational domains: Radar, Electronic Warfare (EW), Satellite Reconnaissance (IMINT), Cyber Threat Intelligence, Human Intelligence (HUMINT), and Friendly Blue Force Tracking (BFT).
* **FR-002**: System MUST expose a pre-joined analytical view `v_multi_domain_intelligence` in BigQuery that correlates multi-sensor data by `target_id` and `track_id`.
* **FR-003**: System MUST provide deterministic pre-LLM regex interceptors that evaluate basic greetings and readiness queries in $\le 50\text{ ms}$ with zero token consumption.
* **FR-004**: System MUST implement the ReAct execution pattern using Google Agent Developer Kit (ADK 2.0) with `gemini-3.8-flash` and `thinking_level="LOW"`.
* **FR-005**: Agent runtime MUST intercept database schema exceptions and autonomously re-issue corrected SQL queries.
* **FR-006**: Structured database interactions MUST be decoupled from agent compute by routing through a Model Context Protocol (MCP) server.
* **FR-007**: System MUST implement a 3-state Circuit Breaker (`CLOSED`, `OPEN`, `HALF_OPEN`) with exponential backoff on all external tool integrations.
* **FR-008**: System MUST configure dual telemetry: OpenTelemetry semantic spans exported to Cloud Trace, and un-elided prompt/response audit logs (`EVENT_ONLY`) exported to Cloud Logging.
* **FR-009**: Model responses MUST be inspected by an inline `after_model_callback` before presentation to the user.
* **FR-010**: System MUST detect Military Grid Reference System (MGRS) tactical coordinates and replace them with `[CUSTOM_MGRS_COORDINATES]` (bypassed if `identity_type == "AGENT_IDENTITY"`).
* **FR-011**: System MUST intercept all kinetic engagement advisories, holding execution under `[HUMAN-IN-THE-LOOP HOLD REQUIRED]` until a valid cryptographic token (`AUTH_<HASH>`) is provided.
* **FR-012**: System MUST integrate Google Cloud Discovery Engine to perform semantic vector search over multimodal HUMINT PDF dossiers with `maxExtractiveSegmentCount: 2`.
* **FR-013**: System MUST format all unstructured intelligence citations as Markdown deep links with page-level anchors.
* **FR-014**: When static context exceeds 32,768 tokens, the system MUST create and reuse a Vertex AI `CachedContent` resource in `location="global"`.
* **FR-015**: System MUST provide an automated offline evaluation script executing Vertex AI `EvalTask`.
* **FR-016**: System MUST expose an Agent-to-Agent (A2A) JSON-RPC 2.0 federation endpoint publishing an Agent Card.

---

## 4. Success Criteria

### 4.1. Measurable Outcomes
* **SC-001**: **Deterministic Fast-Path Latency:** 100% of basic status requests MUST resolve in $\le \mathbf{50\text{ ms}}$ consuming zero LLM tokens.
* **SC-002**: **P95 Analytical Query Latency:** Complex multi-domain queries MUST complete with a 95th percentile latency of $\le \mathbf{3.5\text{ seconds}}$.
* **SC-003**: **Context Caching Cost Reduction:** Sessions utilizing server-side cached context MUST demonstrate a $\ge \mathbf{75\%}$ reduction in input token processing cost.
* **SC-004**: **Context Caching Time-to-First-Token (TTFT):** Multi-turn sessions with active context cache MUST achieve a TTFT of $< \mathbf{1.0\text{ second}}$.
* **SC-005**: **OPSEC Coordinate Leakage Rate:** Model responses MUST achieve a $\mathbf{0.0\%}$ leakage rate for raw MGRS coordinates across external boundaries.
* **SC-006**: **Human-in-the-Loop Doctrinal Safety:** 100% of kinetic strike advisories MUST be intercepted.
* **SC-007**: **Offline Evaluation Benchmark Score:** The agent MUST achieve an aggregate score of $\ge \mathbf{4.5 / 5.0}$ across the 7 Quality Dimensions.
* **SC-008**: **Dual Telemetry Collection Integrity:** 100% of agent reasoning turns MUST emit OpenTelemetry spans and un-elided audit logs.
