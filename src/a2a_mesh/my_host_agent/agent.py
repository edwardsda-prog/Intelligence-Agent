import os
import sys
import re
import json

import subprocess

def find_repo_root(start_dir):
    curr = os.path.abspath(start_dir)
    while curr and curr != "/":
        if os.path.exists(os.path.join(curr, "common")):
            return curr
        curr = os.path.dirname(curr)
    return os.path.abspath(os.path.join(start_dir, "../.."))

MY_AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = find_repo_root(MY_AGENT_DIR)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from common.resilience import CircuitBreaker, retry_with_backoff
from common.hitl import evaluate_hitl_guardrail
from google.adk.agents import Agent
from google.adk.integrations.agent_registry import AgentRegistry
from google.adk.models.google_llm import Gemini
from .observability import instrument_a2a_span, log_a2a_telemetry

def get_default_project_id():
    pid = os.environ.get("PROJECT_ID")
    if pid and pid != "(unset)":
        return pid
    try:
        pid = subprocess.check_output(['gcloud', 'config', 'get-value', 'project'], stderr=subprocess.DEVNULL).decode().strip()
        if pid and pid != "(unset)":
            return pid
    except Exception:
        pass
    return "284046449012"

PROJECT_ID = get_default_project_id()
LOCATION = os.environ.get("LOCATION", "global")
MODEL_NAME = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")

# 1. Connect to BigQuery MCP via Agent Registry with Resilience
bq_cb = CircuitBreaker("a2a_bigquery_mcp", failure_threshold=3, recovery_timeout_sec=30.0)

try:
    if not PROJECT_ID:
        raise ValueError("PROJECT_ID environment variable is not set.")
    agent_registry = AgentRegistry(project_id=PROJECT_ID, location=LOCATION)
    import google.adk.integrations.agent_registry.agent_registry as ar_module
    ar_module.AGENT_REGISTRY_BASE_URL = "https://agentregistry.googleapis.com/v1alpha"
    mcp_toolset = agent_registry.get_mcp_toolset(f"projects/{PROJECT_ID}/locations/{LOCATION}/services/bigquery-mcp")
except Exception as e:
    print(f"⚠️ Agent Registry MCP toolset notice: {e}. Using BigQuery direct connection.")
    from google.adk.tools import FunctionTool
    @retry_with_backoff(max_attempts=3, initial_delay=1.0, factor=2.0, circuit_breaker=bq_cb, fallback=lambda q: "⚠️ Live BQ query unavailable; fallback telemetry returned.")
    def execute_bigquery_sql(sql_query: str) -> str:
        """Executes a SQL query against BigQuery dataset mission_data."""
        from google.cloud import bigquery
        client = bigquery.Client(project=PROJECT_ID)
        query_job = client.query(sql_query)
        results = [dict(row) for row in query_job.result()]
        return str(results)
    mcp_toolset = FunctionTool(execute_bigquery_sql)

import subprocess
from google.oauth2.credentials import Credentials

credentials = None
try:
    token = subprocess.check_output(['gcloud', 'auth', 'print-access-token'], stderr=subprocess.DEVNULL).decode('utf-8').strip()
    if token:
        credentials = Credentials(token=token)
except Exception:
    credentials = None

client_kwargs = {
    "enterprise": True,
    "project": PROJECT_ID,
    "location": "global"
}
if credentials:
    client_kwargs["credentials"] = credentials

# 2. Configure Gemini LLM
gemini_model = Gemini(
    model=MODEL_NAME,
    client_kwargs=client_kwargs
)

# 3. Model Armor OPSEC Filter for A2A Releasability

# SCENARIO 7 OBJECTIVE: Agent-to-Agent (A2A) Federation & Gateway Governance.
# This Host Agent applies Model Armor to redact raw coordinates before sharing data with Coalition Partners.
# SCENARIO 7 OBJECTIVE: Agent-to-Agent (A2A) Federation & Gateway Governance.
# This Host Agent applies Model Armor to redact raw coordinates before sharing data with Coalition Partners.
def sanitize_a2a_response(raw_text: str, inbound_prompt: str = "") -> str:
    """
    Applies OPSEC Model Armor redaction rules via the Google Cloud Model Armor API:
    Redacts raw military MGRS grid coordinates (e.g. 30UGC9914906064) before transmitting A2A responses to coalition partners.
    Also validates Human-in-the-Loop authorization before releasing kinetic advisories across coalition boundaries.
    """
    # HITL Secure Gate check for A2A cross-domain dissemination or kinetic invocation
    combined_check = f"{inbound_prompt} {raw_text}".upper()
    for high_consequence in ["KINETIC_ENGAGEMENT", "STRIKE ADVISORY", "OFFENSIVE_CYBER", "KINETIC STRIKE", "MISSILE SALVO", "FIRE_AUTHORIZATION"]:
        if high_consequence in combined_check:
            tgt_match = re.search(r'(TGT-[A-Z0-9\-]+)', combined_check, re.IGNORECASE)
            tgt_id = tgt_match.group(1).upper() if tgt_match else "UNKNOWN_TARGET"
            decision = evaluate_hitl_guardrail("KINETIC_ENGAGEMENT", {"target_id": tgt_id})
            if decision.get("status") == "HELD":
                return f"403 FORBIDDEN: SECURE_KINETIC_CONTROL_RESERVED - {decision.get('message')}"
    import requests, google.auth, google.auth.transport.requests
    try:
        project_id = os.environ.get("PROJECT_ID", "284046449012")
        location = os.environ.get("LOCATION", "us-central1")
        
        try:
            creds, _ = google.auth.default()
            auth_req = google.auth.transport.requests.Request()
            creds.refresh(auth_req)
            token = creds.token
        except Exception:
            token = subprocess.check_output(['gcloud', 'auth', 'print-access-token'], stderr=subprocess.DEVNULL).decode('utf-8').strip()
        
        url = f"https://modelarmor.{location}.rep.googleapis.com/v1/projects/{project_id}/locations/{location}/templates/mission_intel_armor:sanitizeModelResponse"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-Goog-User-Project": project_id
        }
        body = {
            "modelResponseData": {
                "text": raw_text
            }
        }
        res = requests.post(url, headers=headers, json=body, timeout=5)
        if res.status_code == 200:
            resp_data = res.json()
            sdp_text = (
                resp_data.get("sanitizationResult", {})
                .get("filterResults", {})
                .get("sdp", {})
                .get("sdpFilterResult", {})
                .get("deidentifyResult", {})
                .get("data", {})
                .get("text")
            )
            sanitized = sdp_text or resp_data.get("modelResponseData", {}).get("text", raw_text)
            # Format token for NATO releasability
            sanitized = sanitized.replace("[CUSTOM_MGRS_COORDINATES]", "[REDACTED_MGRS_COORDINATE_NATO_RELEASABLE]")
            return sanitized
    except Exception as e:
        print(f"Model Armor API Error: {e}")
        
    # Fallback to regex if API fails
    mgrs_pattern = r'\b\d{1,2}[C-X][A-HJ-NP-Z]{2}\d{6,10}\b'
    return re.sub(mgrs_pattern, '[REDACTED_MGRS_COORDINATE_NATO_RELEASABLE]', raw_text)

# 4. Host Agent Processing A2A Requests
root_agent = Agent(
    model=gemini_model,
    name="learning_lab_a2a_host_agent",
    instruction=(
        f"You are the Mission Intel Host Mission Intelligence Agent servicing Agent-to-Agent (A2A) queries "
        f"from NATO Coalition Partner Agents.\n\n"
        f"You have direct access to BigQuery dataset `{PROJECT_ID}.mission_data` via an MCP server.\n"
        "TABLE SCHEMAS & KEY COLUMNS:\n"
        f"1. `{PROJECT_ID}.mission_data.v_multi_domain_intelligence`: Pre-joined view (`track_id`, `target_id`, `radar_signature`, `ew_bearing`, `cyber_actor`, `humint_content`, `friendly_unit`).\n"
        f"2. `{PROJECT_ID}.mission_data.radar_telemetry`: (`track_id`, `platform_type`, `signature`, `target_id`, `velocity_knots`, `mgrs_coord`).\n"
        f"3. `{PROJECT_ID}.mission_data.ew_intercepts` / `ew_bearings`: (`ew_id`, `bearing_degrees`, `signal_frequency_ghz`, `prf_khz`, `emitter_type`, `threat_level`, `track_id`, `target_id`).\n"
        f"4. `{PROJECT_ID}.mission_data.satellite_recon`: (`image_id`, `target_id`, `sensor_type`, `detected_structures_units`, `confidence_score`).\n"
        f"5. `{PROJECT_ID}.mission_data.cyber_threat_intel`: (`event_id`, `target_system`, `threat_actor`, `indicator_of_compromise`, `status`, `target_id`).\n"
        f"6. `{PROJECT_ID}.mission_data.friendly_assets`: (`asset_id`, `unit_name`, `callsign`, `assigned_sector`, `defensive_perimeter`).\n\n"
        "A2A PROTOCOL RULES:\n"
        "- Respond concisely and professionally to coalition intelligence requests.\n"
        "- Data classification for coalition export is 'Demonstrator // REL TO NATO'.\n"
        "- Protect raw coordinates and sensitive US-ONLY cyber indicators."
    ),
    tools=[mcp_toolset]
)

def process_a2a_inbound_query(a2a_json_payload: str) -> str:
    """
    Entrypoint for processing incoming A2A JSON-RPC requests from Allied Coalition Agents.
    """
    try:
        data = json.loads(a2a_json_payload)
        params = data.get("params", {})
        prompt = params.get("prompt", "")
        caller_id = params.get("caller_identity", "UNKNOWN_COALITION_PARTNER")
        req_id = data.get("id", "req-0")

        log_a2a_telemetry("a2a_query_received", {"caller_identity": caller_id, "prompt": prompt})

        with instrument_a2a_span(caller_id, prompt):
            # In live production, ADK agent runner executes the query
            # Here we simulate the A2A processing turn and OPSEC filter
            raw_response = (
                f"Mission Intel Intelligence Report for {caller_id}:\n"
                f"Target TGT-ALPHA-7 (Project 22800 Corvette) tracked via TRK-901 at position 30UGC9914906064. "
                "Radar emitting Mineral-ME signature at 9.41 GHz on bearing 145.2°. "
                "Friendly asset HMS Defender (SENTINEL-1) is maintaining a 60nm defensive perimeter."
            )
            
            # Apply OPSEC Model Armor Redaction and Secure Kinetic Gate
            sanitized_response = sanitize_a2a_response(raw_response, inbound_prompt=prompt)
            
            log_a2a_telemetry("a2a_query_completed", {
                "caller_identity": caller_id,
                "sanitized": True,
                "response_length": len(sanitized_response)
            })
            
            response_payload = {
                "jsonrpc": "2.0",
                "result": {
                    "response": sanitized_response,
                    "classification_tag": "Demonstrator // REL TO NATO",
                    "host_agent": "learning_lab_a2a_host_agent"
                },
                "id": req_id
            }
            return json.dumps(response_payload, indent=2)
    except Exception as e:
        return json.dumps({"jsonrpc": "2.0", "error": {"code": -32603, "message": str(e)}, "id": None})
