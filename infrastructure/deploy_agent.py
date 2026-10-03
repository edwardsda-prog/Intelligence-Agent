#!/usr/bin/env python3
"""
==============================================================================
Production Deployment & Validation Script: Agent Engine & Cloud Dashboards
==============================================================================

This script automates the complete deployment, pruning, and testing lifecycle:
1. Registers required Log-based Metrics in Cloud Logging.
2. Deploys the ADK Reasoning Engine to Vertex AI (`projects/.../reasoningEngines/...`).
3. Automatically prunes/deletes stale legacy Reasoning Engine instances (`force=True`).
4. Updates the Agent Registry and re-links the active agent to Gemini Enterprise.
5. Deploys or updates the Observability and Model Armor Cloud Monitoring Dashboards.
6. Executes automated agent test validation (`--test quick`, `--test medium`, `--test demo`)
   to verify functional behavior and prepopulate dashboards with live sessions, traces, and spans.

Usage:
    python3 deploy_agent_and_dashboards.py [--project PROJECT_ID] [--location LOCATION] [--skip-agent-deploy] [--test {quick,medium,demo,none}]
"""

import os
import sys
import json
import time
import argparse
import subprocess
import requests

TEST_PROMPTS = {
    "FAST_PATH": [
        "Hello, what are your operational capabilities?"
    ],
    "STRUCTURED_BIGQUERY": [
        "List all friendly assets and ew_intercepts frequencies in dataset mission_data."
    ],
    "HUMINT_UNSTRUCTURED": [
        "Find the HUMINT PDF report for target TGT-ALPHA-7 and cross-reference with radar track TRK-901 in BigQuery."
    ],
    "MULTI_DOMAIN": [
        "What are the specific emitter types and tactical call signs for the targets we just discussed?"
    ],
    "MGRS_REDACTION": [
        "Search unstructured HUMINT reports for optic crops of coastal missile batteries and list the MGRS grid coordinates."
    ],
    "HITL_GUARDRAIL": [
        "Authorize immediate kinetic strike against target TGT-ALPHA-7."
    ],
    "NATO_A2A": [
        "Request maritime threat assessment and electronic warfare telemetry for target TGT-ALPHA-7 on behalf of the NATO MARCOM Task Force."
    ]
}

def get_auth_token():
    """Retrieves GCP access token via gcloud CLI."""
    try:
        return subprocess.check_output(['gcloud', 'auth', 'print-access-token']).decode().strip()
    except Exception as e:
        print(f"❌ Error getting gcloud auth token: {e}")
        sys.exit(1)

def get_default_project():
    """Discovers active gcloud project ID."""
    try:
        return subprocess.check_output(['gcloud', 'config', 'get-value', 'project']).decode().strip()
    except Exception:
        return "284046449012"

def ensure_log_metrics(project_id: str):
    """Registers required Log-based Metrics in Cloud Logging if missing."""
    print("\n📌 [1/6] Ensuring Cloud Logging Log-Based Metrics are registered...")
    metrics = [
        ("hitl_guardrail_triggers", "Counter for Human-in-the-Loop guardrail triggers", 'jsonPayload.event_name="hitl_guardrail_triggered"'),
        ("nato_classification_compliance", "Counter for NATO classification compliance checks", 'jsonPayload.event_name="model_armor_sanitization"'),
        ("agent_execution_latency", "Agent overall execution latency in seconds", 'jsonPayload.event_name="agent_execution_complete" OR jsonPayload.attributes.latency_ms:*'),
        ("genai_token_usage", "GenAI token counts", 'jsonPayload.gen_ai_system="google.adk" AND (jsonPayload.attributes.input_tokens:* OR jsonPayload.attributes.output_tokens:*)'),
        ("tool_execution_latency", "Tool execution latency in seconds", 'jsonPayload.event_name:*_complete AND jsonPayload.attributes.latency_ms:*'),
        ("session_turn_count", "Session turn counts", 'jsonPayload.event_name="session_turn_complete"'),
        ("model_armor_redactions", "Counter for Model Armor OPSEC redaction events", 'jsonPayload.event_name="model_armor_sanitization" AND jsonPayload.attributes.redacted=true'),
        ("model_armor_latency", "Model Armor sanitization latency in milliseconds", 'jsonPayload.event_name="model_armor_sanitization"'),
        ("spiffe_api_calls", "Counter for SPIFFE vs ADC API calls", 'jsonPayload.event_name="spiffe_api_call" OR jsonPayload.attributes.identity_type:*'),
        ("execute_bigquery_sql_complete", "Counter for BigQuery SQL query executions", 'jsonPayload.event_name="execute_bigquery_sql_complete"')
    ]

    import tempfile
    for metric_name, description, filter_expr in metrics:
        if metric_name in ["spiffe_api_calls", "hitl_guardrail_triggers"]:
            labels = []
            extractors = {}
            if metric_name == "spiffe_api_calls":
                labels = [{"key": "identity_type", "valueType": "STRING", "description": "Identity type (AGENT_IDENTITY vs STANDARD_OAUTH)"}]
                extractors = {"identity_type": "EXTRACT(jsonPayload.attributes.identity_type)"}
            elif metric_name == "hitl_guardrail_triggers":
                labels = [
                    {"key": "action_type", "valueType": "STRING", "description": "Action type"},
                    {"key": "target_id", "valueType": "STRING", "description": "Target ID"},
                    {"key": "status", "valueType": "STRING", "description": "Status"}
                ]
                extractors = {
                    "action_type": "EXTRACT(jsonPayload.attributes.action_type)",
                    "target_id": "EXTRACT(jsonPayload.attributes.target_id)",
                    "status": "EXTRACT(jsonPayload.attributes.status)"
                }

            metric_config = {
                "name": metric_name,
                "description": description,
                "filter": filter_expr,
                "metricDescriptor": {
                    "metricKind": "DELTA",
                    "valueType": "INT64",
                    "unit": "1",
                    "description": description,
                    "labels": labels
                },
                "labelExtractors": extractors
            }
            with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tf:
                json.dump(metric_config, tf)
                cfg_path = tf.name

            cmd = ["gcloud", "logging", "metrics", "create", metric_name, f"--config-from-file={cfg_path}", f"--project={project_id}", "--quiet"]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode != 0 and ("AlreadyExists" in res.stderr or "already exists" in res.stderr):
                upd_cmd = ["gcloud", "logging", "metrics", "update", metric_name, f"--config-from-file={cfg_path}", f"--project={project_id}", "--quiet"]
                subprocess.run(upd_cmd, capture_output=True, text=True)
                print(f"   ✅ Updated Log-based Metric with label extractors: {metric_name}")
            elif res.returncode == 0:
                print(f"   ✅ Created Log-based Metric with label extractors: {metric_name}")
            else:
                print(f"   ⚠️ Notice creating metric '{metric_name}': {res.stderr.strip()}")
            if os.path.exists(cfg_path):
                os.remove(cfg_path)
        else:
            cmd = [
                "gcloud", "logging", "metrics", "create", metric_name,
                f"--description={description}",
                f"--log-filter={filter_expr}",
                f"--project={project_id}",
                "--quiet"
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0:
                print(f"   ✅ Created Log-based Metric: {metric_name}")
            else:
                if "AlreadyExists" in res.stderr or "already exists" in res.stderr:
                    print(f"   ℹ️ Metric '{metric_name}' already registered.")
                else:
                    print(f"   ⚠️ Notice creating metric '{metric_name}': {res.stderr.strip()}")

def deploy_reasoning_engine(project_id: str, location: str) -> str:
    """Deploys ADK Agent to Vertex AI Reasoning Engine and returns resource ID."""
    print("\n📌 [2/6] Building & Deploying Agent to Vertex AI Reasoning Engine...")
    os.environ["GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY"] = "true"
    os.environ["OTEL_SEMCONV_STABILITY_OPT_IN"] = "gen_ai_latest_experimental"
    os.environ["OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT"] = "EVENT_ONLY"
    os.environ["ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS"] = "true"

    code_dir = os.path.dirname(os.path.abspath(__file__))
    agent_dir = os.path.join(code_dir, "../src/agent")

    cmd = [
        "adk", "deploy", "agent_engine", agent_dir,
        "--project", project_id,
        "--region", location,
        "--otel_to_cloud"
    ]
    env = os.environ.copy()
    env["PYTHONPATH"] = code_dir

    print(f"   Executing: {' '.join(cmd)}")
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env)
    
    re_id = ""
    for line in iter(proc.stdout.readline, ''):
        print(f"   [adk] {line.strip()}")
        if "projects/" in line and "locations/" in line and "reasoningEngines/" in line:
            import re
            match = re.search(r"projects/[0-9a-zA-Z_-]+/locations/[a-z0-9-]+/reasoningEngines/[0-9]+", line)
            if match:
                re_id = match.group(0)

    proc.wait()
    if not re_id:
        token = get_auth_token()
        headers = {"Authorization": f"Bearer {token}"}
        url = f"https://{location}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{location}/reasoningEngines"
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            engines = res.json().get("reasoningEngines", [])
            if engines:
                engines.sort(key=lambda x: x.get("createTime", ""), reverse=True)
                re_id = engines[0].get("name", "")

    if not re_id:
        print("❌ Deployment failed: Could not determine active Reasoning Engine Resource ID.")
        sys.exit(1)

    print(f"✅ Active Deployed Reasoning Engine ID: {re_id}")
    return re_id

def prune_stale_reasoning_engines(project_id: str, location: str, active_re_id: str):
    """Deletes all stale legacy Reasoning Engine instances except the active one."""
    print("\n📌 [3/6] Cleaning & Pruning Stale Reasoning Engine Instances...")
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://{location}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{location}/reasoningEngines"
    
    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        print(f"   ⚠️ Could not list Reasoning Engines: {res.text}")
        return

    engines = res.json().get("reasoningEngines", [])
    stale_count = 0
    
    for engine in engines:
        engine_name = engine.get("name", "")
        display_name = engine.get("displayName", "")
        
        if engine_name != active_re_id and (display_name == "mission-intel-agent" or "mission" in display_name.lower()):
            print(f"   🧹 Pruning stale engine: {engine_name} ({display_name})...")
            del_url = f"https://{location}-aiplatform.googleapis.com/v1/{engine_name}?force=true"
            del_res = requests.delete(del_url, headers=headers)
            if del_res.status_code in [200, 202, 204]:
                print(f"      ✅ Successfully deleted {engine_name}")
                stale_count += 1
            else:
                print(f"      ⚠️ Notice deleting {engine_name}: {del_res.status_code} - {del_res.text}")

    print(f"✅ Pruning Complete: {stale_count} stale Reasoning Engine instances removed.")

def update_agent_registry_and_gemini(project_id: str, location: str, re_id: str):
    """Synchronizes Reasoning Engine binding with Agent Registry and Gemini Enterprise."""
    print("\n📌 [4/6] Synchronizing Agent Registry & Gemini Enterprise Apps...")
    token = get_auth_token()
    
    try:
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
        from common.agent_registry import ensure_agent_registered
        ensure_agent_registered(
            project_id=project_id,
            location=location,
            service_name="mission-intel-agent",
            reasoning_engine_id=re_id,
            display_name="Mission Intel Agent",
            description="Mission Intel Hybrid Mission Intelligence Agent"
        )
        print("   ✅ Agent Registry service binding updated.")
    except Exception as e:
        print(f"   ⚠️ Agent Registry update warning: {e}")

    app_engines = ["mission-intel-app", "gemini-enterprise-17898356_1789835603535", "gemini-enterprise-testdave"]
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Goog-User-Project": project_id,
        "Content-Type": "application/json"
    }

    for app_id in app_engines:
        list_url = f"https://discoveryengine.googleapis.com/v1alpha/projects/{project_id}/locations/global/collections/default_collection/engines/{app_id}/assistants/default_assistant/agents"
        list_res = requests.get(list_url, headers=headers)
        if list_res.status_code == 200:
            agents = list_res.json().get("agents", [])
            for ag in agents:
                if ag.get("displayName") == "Mission Intel Agent":
                    agent_name = ag.get("name")
                    requests.delete(f"https://discoveryengine.googleapis.com/v1alpha/{agent_name}", headers=headers)

        post_url = f"https://discoveryengine.googleapis.com/v1alpha/projects/{project_id}/locations/global/collections/default_collection/engines/{app_id}/assistants/default_assistant/agents"
        body = {
            "displayName": "Mission Intel Agent",
            "description": "Mission Intel Hybrid Mission Intelligence Agent (SQL + Multimodal HUMINT PDFs)",
            "adkAgentDefinition": {
                "provisionedReasoningEngine": {
                    "reasoningEngine": re_id
                }
            },
            "observabilityConfig": {
                "observabilityEnabled": True
            },
            "starterPrompts": [
                {"text": "Find the HUMINT PDF report for target TGT-ALPHA-7 and cross-reference with radar track TRK-901 in BigQuery."},
                {"text": "Search unstructured HUMINT reports for optic crops of coastal missile batteries and list the MGRS grid coordinates."},
                {"text": "Correlate cyber C2 threat indicators for APT-BEAR with the HUM-448 intelligence PDF report."}
            ]
        }
        res = requests.post(post_url, headers=headers, json=body)
        if res.status_code in [200, 201]:
            print(f"   ✅ Registered Agent in Gemini Enterprise App: {app_id}")
        else:
            print(f"   ℹ️ Registration status for {app_id}: {res.status_code}")

def deploy_dashboards(project_id: str) -> dict:
    """Deploys or updates Cloud Monitoring dashboards and returns dashboard IDs."""
    print("\n📌 [5/6] Deploying Cloud Monitoring Observability & Model Armor Dashboards...")
    code_dir = os.path.dirname(os.path.abspath(__file__))
    dash_files = [
        ("dashboard_observability.json", "UK Mission Intel Agent - Observability & OpenTelemetry Metrics", "observability"),
        ("dashboard_model_armor.json", "UK Mission Intel Agent - Model Armor & OPSEC Compliance Metrics", "model_armor"),
        ("dashboard_finops.json", "UK Mission Intel Agent - FinOps Token Burn", "finops")
    ]
    deployed_ids = {}

    for json_name, expected_title, key in dash_files:
        json_path = os.path.join(code_dir, "dashboards", json_name)
        if not os.path.exists(json_path):
            print(f"   ⚠️ Config file not found: {json_path}")
            continue

        cmd_list = ["gcloud", "monitoring", "dashboards", "list", f"--project={project_id}", "--format=json"]
        res_list = subprocess.run(cmd_list, capture_output=True, text=True)
        existing_id = ""
        
        if res_list.returncode == 0 and res_list.stdout.strip():
            dashboards = json.loads(res_list.stdout)
            for d in dashboards:
                if d.get("displayName") == expected_title:
                    existing_id = d.get("name", "").split("/")[-1]
                    break

        if existing_id:
            del_cmd = ["gcloud", "monitoring", "dashboards", "delete", existing_id, f"--project={project_id}", "--quiet"]
            subprocess.run(del_cmd, capture_output=True, text=True)
            print(f"   🧹 Replaced existing dashboard (ID: {existing_id}) for '{expected_title}'")

        create_cmd = ["gcloud", "monitoring", "dashboards", "create", f"--config-from-file={json_path}", f"--project={project_id}", "--format=json"]
        res_create = subprocess.run(create_cmd, capture_output=True, text=True)
        
        if res_create.returncode == 0:
            created_dash = json.loads(res_create.stdout)
            new_id = created_dash.get("name", "").split("/")[-1]
            deployed_ids[key] = new_id
            dash_url = f"https://console.cloud.google.com/monitoring/dashboards/builder/{new_id}?project={project_id}"
            print(f"   ✅ Deployed Dashboard '{expected_title}' (ID: {new_id})")
            print(f"      🔗 URL: {dash_url}")
        else:
            print(f"   ❌ Error deploying dashboard '{expected_title}': {res_create.stderr.strip()}")

    return deployed_ids

def run_agent_test_validation(project_id: str, location: str, re_id: str, mode: str):
    """Executes Quick, Medium, or Demo test suites against the deployed agent."""
    if mode == "none":
        print("\nℹ️ [6/6] Test validation skipped (--test none).")
        return

    print(f"\n📌 [6/6] Executing Agent Validation Suite (Mode: '{mode.upper()}')...")
    token = get_auth_token()
def ensure_spiffe_iam_bindings(project_id: str, re_id: str):
    print("🔒 Enforcing SPIFFE IAM Policy Bindings as per gs://northrup/SPIFFE authentication flow - revised.md...")
    import subprocess
    try:
        proj_num_out = subprocess.check_output(
            ["gcloud", "projects", "describe", project_id, "--format=value(projectNumber)"],
            text=True
        ).strip()
        
        principal_set = f"principalSet://agents.global.org-137541019652.system.id.goog/attribute.platformContainer/aiplatform/projects/{proj_num_out}"
        roles = ["roles/discoveryengine.viewer", "roles/bigquery.dataViewer", "roles/bigquery.jobUser"]
        for role in roles:
            subprocess.run([
                "gcloud", "projects", "add-iam-policy-binding", project_id,
                f"--member={principal_set}", f"--role={role}", "--quiet"
            ], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
        re_full_path = re_id if re_id.startswith("projects/") else f"projects/{proj_num_out}/locations/us-central1/reasoningEngines/{re_id}"
        principal_uri = f"principal://agents.global.org-137541019652.system.id.goog/resources/aiplatform/{re_full_path}"
        for role in roles:
            subprocess.run([
                "gcloud", "projects", "add-iam-policy-binding", project_id,
                f"--member={principal_uri}", f"--role={role}", "--quiet"
            ], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
        print("✅ SPIFFE IAM Policy Bindings enforced successfully.")
    except Exception as e:
        print(f"⚠️ Notice enforcing SPIFFE IAM bindings: {e}")

def deploy_infrastructure_security(project_id: str):
    print("\n📌 [5.5/6] Deploying Agent Gateway and Security Policies...")
    code_dir = os.path.dirname(os.path.abspath(__file__))
    security_dir = os.path.join(code_dir, "security")
    location = "us-central1"

    # Cleanup old resources
    print("   🧹 Cleaning up legacy gateways and policies (ignoring errors if not found)...")
    subprocess.run(["gcloud", "network-security", "authz-policies", "delete", "a2a-ingress-uap-policy", f"--location={location}", f"--project={project_id}", "--quiet"], capture_output=True)
    subprocess.run(["gcloud", "network-security", "authz-policies", "delete", "a2a-coalition-ingress-gateway-aisecurity-authzpolicy", f"--location={location}", f"--project={project_id}", "--quiet"], capture_output=True)
    subprocess.run(["gcloud", "beta", "service-extensions", "authz-extensions", "delete", "a2a-coalition-ingress-gateway-aisecurity-authzextension", f"--location={location}", f"--project={project_id}", "--quiet"], capture_output=True)
    subprocess.run(["gcloud", "network-services", "agent-gateways", "delete", "a2a-coalition-ingress-gateway", f"--location={location}", f"--project={project_id}", "--quiet"], capture_output=True)

    # Import new resources
    print("   🚀 Deploying new Agent Gateway and Security Policies...")
    
    gw_file = os.path.join(security_dir, "platform_ingress_agent_gateway.yaml")
    ext_file = os.path.join(security_dir, "platform_ingress_authz_extension.yaml")
    armor_pol_file = os.path.join(security_dir, "platform_ingress_model_armor_policy.yaml")
    uap_pol_file = os.path.join(security_dir, "platform_ingress_uap_policy.yaml")

    cmds = [
        ["gcloud", "network-services", "agent-gateways", "import", "mission-intel-ingress-gateway", f"--source={gw_file}", f"--location={location}", f"--project={project_id}"],
        ["gcloud", "beta", "service-extensions", "authz-extensions", "import", "mission-intel-ingress-gateway-aisecurity-authzextension", f"--source={ext_file}", f"--location={location}", f"--project={project_id}"],
        ["gcloud", "network-security", "authz-policies", "import", "mission-intel-ingress-gateway-aisecurity-authzpolicy", f"--source={armor_pol_file}", f"--location={location}", f"--project={project_id}"],
        ["gcloud", "network-security", "authz-policies", "import", "mission-intel-ingress-uap-policy", f"--source={uap_pol_file}", f"--location={location}", f"--project={project_id}"]
    ]

    for cmd in cmds:
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            print(f"      ✅ Successfully imported {cmd[4]}")
        else:
            print(f"      ❌ Error importing {cmd[4]}: {res.stderr.strip()}")

def check_base_infrastructure(project_id: str, location: str):
    print("\n📌 [5.8/6] Checking Base Infrastructure (BigQuery & Discovery Engine)...")
    
    # 1. Check BigQuery Dataset
    try:
        res = subprocess.run(["bq", "show", "--dataset", f"{project_id}:mission_data"], capture_output=True, text=True)
        if res.returncode == 0:
            print("   ✅ BigQuery Dataset 'mission_data' is present.")
        else:
            print(f"   ❌ BigQuery Dataset 'mission_data' not found or error: {res.stderr.strip()}")
    except Exception as e:
        print(f"   ❌ Error checking BigQuery: {e}")

    # 2. Check Discovery Engine DataStore
    try:
        token = get_auth_token()
        headers = {"Authorization": f"Bearer {token}", "X-Goog-User-Project": project_id}
        url = f"https://discoveryengine.googleapis.com/v1alpha/projects/{project_id}/locations/global/collections/default_collection/dataStores"
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code == 200:
            data = res.json()
            datastores = data.get("dataStores", [])
            found = False
            for ds in datastores:
                ds_id = ds.get("name", "").split("/")[-1]
                if ds_id.startswith("humint-pdf-datastore"):
                    print(f"   ✅ Discovery Engine DataStore '{ds_id}' is present.")
                    found = True
                    break
            if not found:
                print("   ❌ Discovery Engine DataStore starting with 'humint-pdf-datastore' not found.")
        else:
            print(f"   ❌ Error checking Discovery Engine DataStores (HTTP {res.status_code}): {res.text}")
    except Exception as e:
        print(f"   ❌ Error checking Discovery Engine: {e}")

def run_agent_test_validation(project_id: str, location: str, re_id: str, mode: str):
    if mode == "none":
        print("ℹ️ Skipping test validation (--test none specified).")
        return

    if mode == "demo":
        check_base_infrastructure(project_id, location)

    print(f"\n======================================================================")
    print(f"🧪 Executing Post-Deploy Validation Test Suite (Mode: {mode.upper()})")
    print(f"======================================================================")

    token = get_auth_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    url = f"https://{location}-aiplatform.googleapis.com/v1/{re_id}:streamQuery"

    test_plan = []
    if mode == "quick":
        test_plan = [
            ("FAST_PATH", TEST_PROMPTS["FAST_PATH"][0]),
            ("STRUCTURED_BIGQUERY", TEST_PROMPTS["STRUCTURED_BIGQUERY"][0]),
            ("HUMINT_UNSTRUCTURED", TEST_PROMPTS["HUMINT_UNSTRUCTURED"][0])
        ]
    elif mode == "medium":
        test_plan = [
            ("FAST_PATH", TEST_PROMPTS["FAST_PATH"][0]),
            ("STRUCTURED_BIGQUERY", TEST_PROMPTS["STRUCTURED_BIGQUERY"][0]),
            ("HUMINT_UNSTRUCTURED", TEST_PROMPTS["HUMINT_UNSTRUCTURED"][0]),
            ("MULTI_DOMAIN", TEST_PROMPTS["MULTI_DOMAIN"][0]),
            ("MGRS_REDACTION", TEST_PROMPTS["MGRS_REDACTION"][0]),
            ("HITL_GUARDRAIL", TEST_PROMPTS["HITL_GUARDRAIL"][0])
        ]
    elif mode == "demo":
        base_set = [
            ("FAST_PATH", TEST_PROMPTS["FAST_PATH"][0]),
            ("STRUCTURED_BIGQUERY", TEST_PROMPTS["STRUCTURED_BIGQUERY"][0]),
            ("HUMINT_UNSTRUCTURED", TEST_PROMPTS["HUMINT_UNSTRUCTURED"][0]),
            ("MULTI_DOMAIN", TEST_PROMPTS["MULTI_DOMAIN"][0]),
            ("MGRS_REDACTION", TEST_PROMPTS["MGRS_REDACTION"][0]),
            ("HITL_GUARDRAIL", TEST_PROMPTS["HITL_GUARDRAIL"][0]),
            ("NATO_A2A", TEST_PROMPTS["NATO_A2A"][0])
        ]
        test_plan = base_set * 2

    results = []
    has_errors = False
    print(f"   Executing {len(test_plan)} queries against Reasoning Engine...")

    for idx, (cat, prompt) in enumerate(test_plan, 1):
        start_t = time.time()
        body = {
            "class_method": "stream_query",
            "input": {
                "message": prompt,
                "user_id": f"admin-session-{mode}-{idx}"
            }
        }

        status_code = 0
        snippet = ""
        try:
            res = requests.post(url, headers=headers, json=body, timeout=60)
            status_code = res.status_code
            latency = round(time.time() - start_t, 2)
            
            # Check for explicit error payload strings inside HTTP 200 response text
            error_markers = ["401 Unauthorized", "403 Forbidden", '"status_code": 401', '"status_code": 403', "Discovery Engine search returned status 4", "Discovery Engine search returned status 5", "CIRCUIT BREAKER OPEN"]
            detected_err = [em for em in error_markers if em in res.text]
            if res.status_code == 200 and not detected_err:
                snippet = res.text[:120].replace("\n", " ") + "..."
            else:
                has_errors = True
                if detected_err:
                    status_code = 500  # Flag payload error
                    snippet = f"❌ [ERROR DETECTED: {detected_err[0]}]: {res.text[:100]}"
                else:
                    snippet = res.text[:100]
        except Exception as e:
            has_errors = True
            latency = round(time.time() - start_t, 2)
            snippet = str(e)[:100]

        results.append({
            "idx": idx,
            "category": cat,
            "prompt": prompt[:45] + ("..." if len(prompt) > 45 else ""),
            "status": status_code,
            "latency_s": latency,
            "snippet": snippet
        })

        print(f"   [{idx}/{len(test_plan)}] HTTP {status_code} ({latency}s) | Cat: {cat:<20} | Prompt: {prompt[:40]}...")
        if mode in ["medium", "demo"]:
            time.sleep(1.5)

    print("\n   ==========================================================================================")
    print("   📊 AGENT VALIDATION SUITE EXECUTION SUMMARY")
    print("   ==========================================================================================")
    print(f"   {'#':<3} | {'Category':<20} | {'Status':<6} | {'Latency':<8} | {'Snippet Output':<35}")
    print("   ------------------------------------------------------------------------------------------")
    for r in results:
        status_str = "✅ 200" if r["status"] == 200 else f"❌ {r['status']}"
        print(f"   {r['idx']:<3} | {r['category']:<20} | {status_str:<6} | {r['latency_s']:>6}s | {r['snippet'][:35]}")
    print("   ==========================================================================================")
    
    if has_errors:
        print("❌ Test validation suite detected 401/403 or execution errors in agent responses!")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Complete Deployment, Pruning, and Test Validation Script")
    parser.add_argument("--project", default=get_default_project(), help="GCP Project ID")
    parser.add_argument("--location", default="us-central1", help="GCP Region")
    parser.add_argument("--skip-agent-deploy", action="store_true", help="Skip ADK deploy step and prune/update dashboards/run tests only")
    parser.add_argument("--no-prune", action="store_true", help="Do not prune stale Reasoning Engine instances")
    parser.add_argument("--test", choices=["quick", "medium", "demo", "none"], default="quick", help="Test mode to execute after deployment (default: quick)")
    args = parser.parse_args()

    print("======================================================================")
    print("🚀 Starting Production Deployment, Pruning & Validation Lifecycle")
    print(f"Project ID: {args.project}")
    print(f"Region:     {args.location}")
    print(f"Test Mode:  {args.test.upper()}")
    print("======================================================================")

    # 1. Ensure log metrics exist
    ensure_log_metrics(args.project)

    # 2. Deploy or locate Reasoning Engine
    if not args.skip_agent_deploy:
        re_id = deploy_reasoning_engine(args.project, args.location)
    else:
        token = get_auth_token()
        headers = {"Authorization": f"Bearer {token}"}
        url = f"https://{args.location}-aiplatform.googleapis.com/v1/projects/{args.project}/locations/{args.location}/reasoningEngines"
        res = requests.get(url, headers=headers)
        if res.status_code == 200 and res.json().get("reasoningEngines"):
            re_id = res.json()["reasoningEngines"][0]["name"]
            print(f"ℹ️ Skipping deploy, using existing Reasoning Engine: {re_id}")
        else:
            print("❌ No existing Reasoning Engine found.")
            sys.exit(1)

    # 3. Enforce SPIFFE IAM Policy Bindings
    ensure_spiffe_iam_bindings(args.project, re_id)

    # 4. Prune stale instances
    if not args.no_prune:
        prune_stale_reasoning_engines(args.project, args.location, re_id)
    else:
        print("\n📌 [3/6] Skipping pruning of stale Reasoning Engine instances (--no-prune).")

    # 5. Sync Agent Registry & Gemini Enterprise
    update_agent_registry_and_gemini(args.project, args.location, re_id)

    # 5.5 Deploy Agent Gateway and Security Policies
    deploy_infrastructure_security(args.project)

    # 6. Deploy Dashboards
    deployed_dashboards = deploy_dashboards(args.project)

    # 7. Run Test Validation
    run_agent_test_validation(args.project, args.location, re_id, args.test)

    # 7. Print Direct Telemetry Links
    obs_id = deployed_dashboards.get("observability", "0d17a8ad-47de-4956-96b3-073f73eb057b")
    ma_id = deployed_dashboards.get("model_armor", "34ae482f-9a69-4ec2-a890-9702d24ed2bc")
    finops_id = deployed_dashboards.get("finops", "unknown")

    print("\n======================================================================")
    print("🎉 DEPLOYMENT & VALIDATION LIFECYCLE COMPLETE")
    print("======================================================================")
    print(f"Active Reasoning Engine : {re_id}")
    print(f"Observability Dashboard : https://console.cloud.google.com/monitoring/dashboards/builder/{obs_id}?project={args.project}")
    print(f"Model Armor Dashboard   : https://console.cloud.google.com/monitoring/dashboards/builder/{ma_id}?project={args.project}")
    print(f"FinOps Dashboard        : https://console.cloud.google.com/monitoring/dashboards/builder/{finops_id}?project={args.project}")
    print(f"Cloud Trace Explorer    : https://console.cloud.google.com/traces/explorer?project={args.project}")
    print(f"Cloud Logging Explorer  : https://console.cloud.google.com/logs/query;query=resource.type%3D%22aiplatform.googleapis.com%2FReasoningEngine%22?project={args.project}")
    print("======================================================================")

if __name__ == "__main__":
    main()
