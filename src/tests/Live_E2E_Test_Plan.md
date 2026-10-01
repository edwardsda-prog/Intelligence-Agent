# 📋 Master Test Plan: End-to-End (E2E) Full-Stack Verification

**Document Status:** DRAFT  
**Author:** Test Management  
**System Under Test (SUT):** Multi-Domain Agentic Intelligence Application  
**Target Environment:** Local Sandbox (SQLite) & Sterile Google Cloud Project (Live APIs)  

---

## 1. Executive Summary & Objective
The objective of this test cycle is to validate the complete deployment, security guardrails, and orchestration capabilities of the Agentic AI ecosystem. This plan covers both the **Local ADK Sandbox (SQLite)** for fast inner-loop validation and the **Live Google Cloud Infrastructure** (BigQuery, Vertex AI, Reasoning Engine, Cloud Run, Model Armor) for production-grade validation.

Crucially, this plan also guarantees **100% accuracy of the Customer Scenario Guides** through a hybrid approach combining automated static cross-referencing and a manual Human User Acceptance Testing (UAT) Dry Run.

## 2. Prerequisites & Entry Criteria
*   **Target Project:** A designated, billing-enabled Google Cloud Project.
*   **Authentication:** The test runner must be authenticated via `gcloud auth login --update-adc` with `Owner` or `Editor` IAM privileges.
*   **Quotas:** Vertex AI (Gemini 3.8 Flash) and Discovery Engine API quotas must be adequate for test loads.
*   **Dependencies:** `gcloud`, `bq`, `python3.11+`, and local dependencies (`pytest`, `google-cloud-aiplatform`, etc.) installed.

---

## 3. Test Execution Phases

### Phase 0: Automated Markdown Verification
**Objective:** Guarantee that the code snippets, SQL queries, and interactive prompts embedded in the Markdown Scenario Guides exactly match the underlying production codebase and test suite without drift.
*   **Action:** Execute the dedicated markdown accuracy test suite.
    ```bash
    python3 tests/test_markdown_accuracy.py
    ```
*   **Success Criteria:** The Python script successfully extracts all code blocks and asserts strict character-for-character parity with `test_prompts.py`, `agent.py`, and infrastructure scripts.

### Phase 1: Sterile Environment Preparation (Teardown)
**Objective:** Eradicate all existing state, both local and in the cloud, to ensure a pristine test baseline.
*   **Action:** Execute the automated teardown script and purge local databases.
    ```bash
    cd <REPO_ROOT>/lab0/code
    bash teardown.sh
    # Manually purge local SQLite state
    rm -f <REPO_ROOT>/lab2/mission_data.db
    ```
*   **Success Criteria:** All BigQuery datasets, Cloud Run services, Agent Registries, and Vertex AI Reasoning Engine instances are deleted. Local databases and DLP templates are wiped.

### Phase 2: System Bootstrap (Clean Setup)
**Objective:** Provision the entire Agentic Data Platform, including both local SQLite structures and Cloud Infrastructure, from zero.
*   **Action:** Execute the unified setup automation.
    ```bash
    cd <REPO_ROOT>
    bash setup.sh
    ```
*   **Success Criteria:** Setup completes with Exit Code `0`. The local SQLite sandbox, BigQuery schemas, Cloud Run MCP containers, and Reasoning Engine agents are fully initialized and registered.

### Phase 3: E2E Execution (Dual-Target)
**Objective:** Execute the 39-point test matrix across both operational environments to guarantee functional parity between developer laptops and production cloud deployment.

#### Phase 3a: Local Mock Verification (SQLite)
*   **Action:** `./test_e2e.sh --mock`
*   **Purpose:** Rapid inner-loop validation against the local SQLite database.

#### Phase 3b: Live Cloud API Verification
*   **Action:** `./test_e2e.sh --live`
*   **Purpose:** Production validation forcing all traffic through actual cloud perimeters (BigQuery, Cloud Run MCP, Model Armor, Agent Gateway).

### Phase 4: Human UAT Dry Run (Console/UI Navigation)
**Objective:** Guarantee 100% accuracy of the UI navigation steps (e.g., clicking through the Google Cloud Console) that cannot be statically parsed.
*   **Action:** A human tester manually walks through Scenarios 1-7 in the sterile Google Cloud Project.
*   **Issue Handling:** If the Google Cloud Console UI has drifted (e.g., a button was renamed), the tester **dynamically fixes the markdown files on the fly** during the execution run, committing the changes without blocking the formal test pipeline.

### Phase 5: Artifact Review & Final Sign-Off
**Objective:** Analyze the test artifacts to determine production release readiness.
*   **Action:** Review the generated scorecards (`tests/test_e2e_report.md` / `.html`).
*   **Success Criteria:**
    *   **100% Pass Rate** on all test vectors across both `--mock` and `--live` executions.
    *   Time-To-First-Token (TTFT) metrics fall within acceptable SLAs.
    *   Zero coordinate leakage on Scenario 4 OPSEC tests.
    *   Tester confirmation that all UI instructions are strictly accurate as of today.

---

## 4. Rollback & Contingency
If the test suite fails during Phase 3, the Test Manager will:
1. Capture all Cloud Trace IDs and Cloud Logging payloads.
2. Halt the pipeline (No-Go).
3. Execute `teardown.sh` to prevent runaway costs from dangling cloud resources.
4. Escalate the specific failed assertions to the Architecture & Development teams.
