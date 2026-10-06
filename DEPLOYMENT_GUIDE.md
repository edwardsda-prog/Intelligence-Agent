# Deployment & Telemetry Guide

Welcome to the Intelligence Agent operations guide! This document explains what happens when you deploy the application and provides clear instructions on how to set it up and populate it with realistic telemetry data for demonstrations.

---

## 1. What You Are Deploying

When you run the deployment script, you are not managing raw servers. You are deploying a managed **Agentic Ecosystem** on Google Cloud. Here is what the script provisions automatically:

1. **Base Infrastructure & Data Provisioning:** The deployment script automatically determines your target project based on your active `gcloud` configuration. It provisions:
   - **BigQuery Datasets:** Creates datasets for `mission_data`, `model_armor_logs`, and `system_logs` (and builds necessary table schemas).
   - **Google Cloud Storage (GCS):** Creates a bucket named `gs://[YOUR_PROJECT_ID]-humint-docs`, uploading **15 unstructured HUMINT PDF reports** and a **JSONL metadata file**.
2. **Discovery Engine (Vertex AI Search):** Provisions an unstructured datastore, imports the HUMINT PDFs via OCR, links it to a Gemini Enterprise App (Intranet search), and enforces Zero-Trust controls by disabling Google Search Grounding.
3. **Data Loss Prevention (DLP) & Model Armor:** Provisions custom templates (`mission_intel_dlp_template`, `a2a_dlp_template`, etc.) to redact PII, MGRS coordinates, tactical call signs, and UK/NATO caveats. It also creates BigQuery log sinks to trace these interceptions.
4. **Vertex AI Reasoning Engine:** The core of the Intelligence Agent. The script packages the Python code (`src/agent/`), prunes any stale legacy instances, and deploys the new code as a managed container handling auto-scaling and built-in memory persistence.
5. **Cloud Logging Metrics:** Automatically registers over 10 GenAI OpenTelemetry log-based metrics (e.g., token usage, agent/tool execution latency, guardrail triggers, and memory operations).
6. **Cloud Monitoring Dashboards:** Provisions four comprehensive dashboards in your GCP project:
   - *Observability & OpenTelemetry Metrics*
   - *Model Armor & OPSEC Compliance Metrics*
   - *FinOps Token Burn*
   - *Agent Platform Memory Metrics*
7. **Agent Validation Testing:** Runs an automated test validation suite upon deployment (configurable via `--test`) to verify functional behavior and pre-populate your new dashboards with live trace data.

---

## 2. Prerequisites

- **Python 3 & Requests**: You must have Python 3 installed on your local machine along with the `requests` library (`pip install requests`).
- **Google Cloud SDK (`gcloud`)**: You must be logged in and configured to your active project (`gcloud auth login` and `gcloud config set project [YOUR_PROJECT_ID]`).
- **Google Agent Developer Kit (ADK)**: Ensure the ADK CLI is installed and available in your environment (`pip install google-adk` or equivalent).

---

## 3. Step-by-Step: How to Deploy

To deploy the entire environment from scratch, hand these exact steps to any developer:

1. **Open your terminal** in the root of the repository.
2. **Ensure you are authenticated** and have your target project set:
   ```bash
   gcloud auth login
   gcloud config set project [YOUR_PROJECT_ID]
   ```
3. **Execute the deployment wrapper script:**
   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```

> **Note:** The `deploy.sh` script automatically runs a quick validation test at the end to ensure the Reasoning Engine is healthy. You can skip this by appending `--test none`.

---

## 4. Step-by-Step: Generating Scenario Telemetry

For demonstration purposes, the Cloud Monitoring Dashboards (Observability, Model Armor, etc.) require live data. Empty graphs aren't useful for a workshop.

We've provided a data generation script that simulates a user having a full conversation with the agent, triggering the exact prompts from the **Trainer_Scenarios.md** document.

1. **Wait for deployment to finish** (from Step 3 above).
2. **Run the scenario data generator:**
   ```bash
   chmod +x generate_scenario_data.py
   ./generate_scenario_data.py
   ```

*This script will securely query your newly deployed Reasoning Engine, trigger Model Armor OPSEC redactions, hit the Human-In-The-Loop guardrails, and wait briefly between prompts to populate your Cloud Monitoring metric charts realistically.*

---

## 5. Verification

To verify that the deployment and telemetry generation were successful:

1. **Verify the Agent:** In the Google Cloud Console, navigate to **Vertex AI > Reasoning Engine**. You should see your active container deployment.
2. **Verify the Telemetry Dashboards:** Navigate to **Monitoring > Dashboards**. Open the *Observability & OpenTelemetry Metrics* and *Model Armor & OPSEC Compliance Metrics* dashboards. You should see active token burn charts and security interception logs.

---

## 6. Offline Evaluation

If you need to evaluate the agent's performance against the 7 Quality Dimensions (e.g. after tweaking the system prompt or adding new documents), you can manually run the LLM-as-a-Judge offline evaluation suite.

1. Ensure you are authenticated and have your project configured.
2. Run the evaluation wrapper script from the root directory:
   ```bash
   ./evaluate.sh
   ```
This script will set up the necessary environment variables and invoke the evaluation against the Golden Data Set, outputting the results to your console.

---

## 7. Teardown & Environment Cleanup

When you are finished with the workshop or demonstration, you can safely decommission the deployed infrastructure to prevent ongoing billing charges. We have provided a comprehensive teardown script that specifically targets workshop resources while preserving core Google Cloud APIs.

1. Ensure you are authenticated and have your project configured.
2. Run the teardown script from the root directory:
   ```bash
   ./infrastructure/teardown.sh
   ```

**What this script deletes from GCP (Verbose Summary):**

* **BigQuery Datasets:** Deletes `mission_data`, `model_armor_logs`, and `system_logs` datasets.
* **Cloud Run Services:** Deletes `bigquery-mcp-server`, `remote-mcp-server`, and `mission-intel-gateway`.
* **Agent Gateway & Registry:** Deletes the `mission-intel-gateway` network service and the `bigquery-mcp` / `mission-intel-a2a-host` Agent Registry entries.
* **Vertex AI Reasoning Engines:** Discovers and deletes all deployed Reasoning Engines in the region.
* **Cloud Storage Buckets:** Deletes `gs://[PROJECT_ID]-humint-docs` and `gs://[PROJECT_ID]-mission-docs` including all their contents.
* **Discovery Engine (Vertex AI Search):** Dynamically discovers and deletes all default collection Apps (Engines) and DataStores.
* **Model Armor & Cloud DLP:** Deletes the `mission_intel_armor` template, as well as the `mission_intel_dlp_template` and `mission_intel_dlp_deidentify_template` DLP templates.
* **Cloud Logging Metrics & Sinks:** Removes the custom GenAI OpenTelemetry log-based metrics (e.g., token usage, latency, triggers) and the `model_armor_bq_sink`.
* **Cloud Monitoring Dashboards:** Deletes the custom UK Mission Intel Agent dashboards (Observability, Model Armor, FinOps, and Memory).
* **Selectively Disables APIs:** Disables workshop-specific APIs (`modelarmor.googleapis.com`, `agentregistry.googleapis.com`, `dlp.googleapis.com`, `networkservices.googleapis.com`) while intentionally preserving core APIs (`aiplatform`, `discoveryengine`, `bigquery`, `run`, `storage`).

The script finishes by running a **Clean-Slate Verification Audit** to confirm all specified resources were successfully decommissioned.
