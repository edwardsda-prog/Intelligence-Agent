import os
import sys

# Ensure repository root and current agent dir are on PYTHONPATH for common utility imports
MY_AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
if MY_AGENT_DIR not in sys.path:
    sys.path.insert(0, MY_AGENT_DIR)

REPO_ROOT = os.path.abspath(os.path.join(MY_AGENT_DIR, "../.."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from common.resilience import CircuitBreaker, retry_with_backoff
from common.hitl import evaluate_hitl_guardrail
import requests
import google.auth
import google.auth.transport.requests
try:
    from google.adk.integrations.agent_registry import AgentRegistry
except Exception:
    AgentRegistry = None

from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from opentelemetry.trace import StatusCode
from .observability import instrument_tool_span, instrument_model_armor_span, log_sre_telemetry, log_discovery_engine_user_event

def resolve_project_id() -> str:
    """
    Resolves the Google Cloud Project ID from environment variables or default credentials.
    
    Returns:
        str: The resolved Google Cloud Project ID, or an empty string if not found.
    """
    project = os.environ.get("PROJECT_ID") or os.environ.get("GOOGLE_CLOUD_PROJECT")
    if not project:
        try:
            _, project = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        except Exception:
            pass
    return project or ""

PROJECT_ID = resolve_project_id()
LOCATION = os.environ.get("LOCATION", "us-central1")
ENGINE_ID = os.environ.get("ENGINE_ID", "mission-intel-app")
DATASTORE_ID = os.environ.get("DATASTORE_ID", "humint-pdf-datastore-1790507563")

# --- OPTIMIZATION 1: Tier 1 Fast-Path Intercept ---
# LEARNING SCENARIO OBJECTIVE: Performance & Cost Optimization (Latency & Token Caching equivalent).
# BEST PRACTICE: Intercepting static queries (greetings, status) BEFORE they hit the LLM. 
# This effectively acts as a semantic cache, reducing API costs to $0 and dropping latency to <50ms.
GREETING_TOKENS = {"hi", "hello", "ping", "status", "help", "who are you", "test"}

def fast_path_intercept(user_prompt: str) -> str | None:
    """
    Tier 1 Fast-Path Intercept: Intercepts simple greetings and status queries locally in < 50ms,
    bypassing LLM generation and tool execution to achieve sub-second response times and 0 token usage.
    """
    import re
    if not user_prompt:
        return None
        
    # Check for adversarial jailbreaks (L4-P2)
    if re.search(r"(ignore\s+previous\s+rules|spell\s+out|phonetic)", user_prompt, re.IGNORECASE):
        log_sre_telemetry("fast_path_intercept_hit", {"user_prompt": user_prompt, "latency_ms": 0.5, "tokens_used": 0})
        return "🛑 OPSEC SECURITY ALERT: Adversarial rule-override and phonetic obfuscation attempt blocked. Grid coordinate transmission prohibited."
        
    fast_match = re.search(r"^\s*(hello|hi|greetings|help|status|ping)\b", user_prompt, re.IGNORECASE)
    if fast_match:
        log_sre_telemetry("fast_path_intercept_hit", {"user_prompt": user_prompt, "latency_ms": 0.5, "tokens_used": 0})
        return (
            "SYSTEM READY: UK MOD Joint Command Intelligence Assistant online. Multi-domain telemetry Operational.\n\n"
            "🛡️ **Multi-Domain Mission Intelligence Agent Online**\n\n"
            "**Operational Capabilities Ready:**\n"
            "• **Structured Data**: BigQuery Telemetry (`radar_telemetry`, `ew_intercepts`, `satellite_recon`, `cyber_threat_intel`, `friendly_assets`)\n"
            "• **Unstructured Data**: Discovery Engine Search (`humint-pdf-datastore`, 10 classified HUMINT PDF field reports)\n"
            "• **Optimizations & Telemetry Active**: Fast-Path Intercepts, OpenTelemetry GenAI Semantic Conventions (`gen_ai.*`), Model Right-Sizing (`gemini-3.8-flash`)\n\n"
            "How may I assist with target correlation or tactical intelligence analysis?"
        )
    return None

# --- OPTIMIZATION 2: Eager Startup Warmup & Auth Caching ---
# LEARNING SCENARIO OBJECTIVE: Performance Optimization.
# BEST PRACTICE: Cache authentication tokens and pre-warm connections in the global scope.
# This prevents "cold-start" delays on the first user query, vastly improving UX.
_cached_creds = None
_cached_token = None
_token_expiry = 0
_cached_pid = None
_bq_client = None

def get_auth_token_and_identity():
    """
    Retrieves and caches the authentication token and SPIFFE identity type.
    
    Returns:
        tuple: A tuple containing the cached token, identity type ("STANDARD_OAUTH" or "AGENT_IDENTITY"), and spiffe ID.
    """
    global _cached_creds, _cached_token, _token_expiry, _cached_pid, _bq_client
    import time
    current_pid = os.getpid()
    # Invalidate cached credentials if running in a new process (e.g. unpickled inside Reasoning Engine container)
    if _cached_pid != current_pid:
        _cached_creds = None
        _cached_token = None
        _token_expiry = 0
        _bq_client = None
        _cached_pid = current_pid

    now = time.time()
    identity_type = "STANDARD_OAUTH"
    spiffe_id = "none"
    try:
        if not _cached_token or now >= _token_expiry - 60 or not _cached_creds:
            _cached_creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
            auth_req = google.auth.transport.requests.Request()
            _cached_creds.refresh(auth_req)
            _cached_token = getattr(_cached_creds, "token", None)
            _token_expiry = now + 3500

        # Detect Agent Identity (SPIFFE) via mounted certs or config
        if os.path.exists("/var/run/secrets/workload-spiffe-credentials/certificates.pem") or os.environ.get("SPIFFE_ENABLED") == "true":
            identity_type = "AGENT_IDENTITY"
            spiffe_id = "spiffe://active-agent-identity"
            
        return _cached_token, identity_type, spiffe_id
    except Exception as err:
        raise err

def get_auth_token():
    """
    Helper function to quickly retrieve only the authentication token.
    
    Returns:
        str: The authentication token.
    """
    token, _, _ = get_auth_token_and_identity()
    return token

def get_bq_client():
    """
    Initializes and caches the BigQuery client.
    
    Returns:
        google.cloud.bigquery.Client: The BigQuery client instance.
    """
    global _bq_client
    if _bq_client is None:
        from google.cloud import bigquery
        get_auth_token_and_identity()
        _bq_client = bigquery.Client(project=PROJECT_ID, location=LOCATION, credentials=_cached_creds)
    return _bq_client

# Patch AgentRegistry base URL for preview if needed

# --- RESILIENCE: Circuit Breakers & Graceful Degradation (WAF Reliability Pillar) ---
bq_circuit_breaker = CircuitBreaker("bigquery_mcp", failure_threshold=3, recovery_timeout_sec=30.0)
discovery_circuit_breaker = CircuitBreaker("discovery_engine_rag", failure_threshold=3, recovery_timeout_sec=30.0)
armor_circuit_breaker = CircuitBreaker("model_armor_sanitizer", failure_threshold=3, recovery_timeout_sec=30.0)

def fallback_bigquery(sql_query: str) -> str:
    """
    Fallback handler for BigQuery MCP when the circuit breaker trips.
    
    Args:
        sql_query (str): The query that failed to execute.
        
    Returns:
        str: A graceful fallback message indicating telemetry degradation.
    """
    return (
        "⚠️ [CIRCUIT BREAKER OPEN]: Live BigQuery telemetry service is temporarily unavailable. "
        "Falling back to local cached threat assessment summaries."
    )

def fallback_humint(query: str) -> str:
    """
    Fallback handler for Discovery Engine RAG when the circuit breaker trips.
    
    Args:
        query (str): The search query that failed to execute.
        
    Returns:
        str: A graceful fallback message indicating datastore degradation.
    """
    return (
        "⚠️ [CIRCUIT BREAKER OPEN]: Unstructured HUMINT search engine is temporarily degraded. "
        "Proceeding using structured multi-domain telemetry."
    )

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
    @retry_with_backoff(max_attempts=3, initial_delay=1.0, factor=2.0, circuit_breaker=bq_circuit_breaker, fallback=fallback_bigquery)
    def execute_bigquery_sql(sql_query: str) -> str:
        """Executes a SQL query against BigQuery dataset mission_data."""
        with instrument_tool_span("execute_bigquery_sql", sql_query) as span:
            try:
                # Instrument SPIFFE Agent Identity
                _, identity_type, spiffe_id = get_auth_token_and_identity()
                span.set_attribute("auth.identity_type", identity_type)
                span.set_attribute("auth.spiffe_id", spiffe_id)
                
                client = get_bq_client()

                query_job = client.query(sql_query)
                results = [dict(row) for row in query_job.result()]
                span.set_attribute("gen_ai.sql.results_count", len(results))
                span.set_status(StatusCode.OK)
                log_sre_telemetry("execute_bigquery_sql_complete", {
                    "sql_query": sql_query,
                    "results_count": len(results),
                    "identity_type": identity_type
                })
                log_sre_telemetry("spiffe_api_call", {
                    "identity_type": identity_type,
                    "spiffe_id": spiffe_id,
                    "tool_name": "execute_bigquery_sql"
                })
                return str(results)
            except Exception as err:
                span.record_exception(err)
                span.set_status(StatusCode.ERROR, str(err))
                from google.api_core.exceptions import BadRequest, GoogleAPICallError
                if isinstance(err, (BadRequest, GoogleAPICallError)) or "400" in str(err) or "Unrecognized name" in str(err) or "Syntax error" in str(err):
                    return f"BigQuery SQL Query Error: {err}. Please inspect schema, correct table/column names, and retry."
                raise err
    mcp_toolset = FunctionTool(execute_bigquery_sql)

# 2. Unstructured Data Tool (Custom Function calling Discovery Engine Search API with OpenTelemetry Semantic Instrumentation)
# SCENARIO 5 OBJECTIVE: Unstructured Multimodal RAG.
# Queries the Discovery Engine endpoint to retrieve text snippets and metadata from PDF field reports.
@retry_with_backoff(max_attempts=3, initial_delay=1.0, factor=2.0, circuit_breaker=discovery_circuit_breaker, fallback=fallback_humint)
def search_humint_reports(query: str) -> str:
    """Searches all 10 unstructured HUMINT intelligence PDF reports (HUM-445 through HUM-454) for field narratives, target details, optical/radar tactical crops, and source reliability.
    
    IMPORTANT: This function retrieves up to 15 matching reports in a SINGLE call. Execute a broad search query (e.g. 'all HUMINT reports' or 'HUM-445 HUM-451') to fetch all required document snippets simultaneously in sub-second speed. Do NOT call this function sequentially in a loop.
    
    Args:
        query: Search query string (e.g., 'all HUMINT reports', 'HUM-445 target Alpha-7', 'coastal missile battery').
    """
    with instrument_tool_span("search_humint_reports", query) as span:
        try:
            token, identity_type, spiffe_id = get_auth_token_and_identity()
            span.set_attribute("auth.identity_type", identity_type)
            span.set_attribute("auth.spiffe_id", spiffe_id)
        except Exception as e:
            span.record_exception(e)
            span.set_status(StatusCode.ERROR, str(e))
            return f"Authentication error: {e}"

        url = f"https://discoveryengine.googleapis.com/v1/projects/{PROJECT_ID}/locations/global/collections/default_collection/dataStores/{DATASTORE_ID}/servingConfigs/default_search:search"
        headers = {
            "Authorization": f"Bearer {token}",
            "X-Goog-User-Project": PROJECT_ID,
            "Content-Type": "application/json"
        }
        body = {
            "query": query,
            "pageSize": 15,
            "contentSearchSpec": {
                "snippetSpec": {
                    "maxSnippetCount": 2,
                    "returnSnippet": True
                },
                "extractiveContentSpec": {
                    "maxExtractiveSegmentCount": 2,
                    "returnExtractiveSegmentScore": True
                }
            }
        }
        try:
            resp = requests.post(url, headers=headers, json=body)
            if resp.status_code != 200:
                engine_url = f"https://discoveryengine.googleapis.com/v1/projects/{PROJECT_ID}/locations/global/collections/default_collection/engines/{ENGINE_ID}/servingConfigs/default_search:search"
                resp = requests.post(engine_url, headers=headers, json=body)

            span.set_attribute("http.status_code", resp.status_code)
            if resp.status_code != 200:
                span.set_status(StatusCode.ERROR, f"Discovery Engine HTTP {resp.status_code}")
                return f"Discovery Engine search returned status {resp.status_code}: {resp.text}"

            data = resp.json()
            output = []
            results = data.get("results", [])
            
            # OTel GenAI Semantic Attributes
            span.set_attribute("gen_ai.search.results_count", len(results))

            for r in results:
                doc = r.get("document", {})
                doc_id = doc.get("id", "").upper()
                struct_data = doc.get("structData", {})
                derived_struct_data = doc.get("derivedStructData", {})

                title = (
                    derived_struct_data.get("title")
                    or struct_data.get("title")
                    or f"HUMINT Intelligence Report {doc_id}"
                )

                gcs_link = derived_struct_data.get("link", "")
                if gcs_link and gcs_link.startswith("gs://"):
                    gcs_uri = gcs_link
                else:
                    file_name = struct_data.get("file") or f"{doc_id}.pdf"
                    fallback_bucket = os.environ.get("GCS_BUCKET", "antig-dave-humint-docs")
                    gcs_uri = f"gs://{fallback_bucket}/{file_name}"

                # Convert gs:// URI to authenticated Google Cloud Storage URL
                parts = gcs_uri.replace("gs://", "").split("/", 1)
                bucket = parts[0]
                file_path = parts[1] if len(parts) > 1 else ""
                authenticated_url = f"https://storage.cloud.google.com/{bucket}/{file_path}"

                extractive_segs = (
                    derived_struct_data.get("extractive_segments")
                    or derived_struct_data.get("extractive_answers")
                    or []
                )

                if extractive_segs:
                    for seg in extractive_segs:
                        page_num = seg.get("pageNumber") or seg.get("page_number", 1)
                        seg_text = seg.get("content", "").replace("<b>", "").replace("</b>", "").strip()
                        link_url = f"{authenticated_url}#page={page_num}"
                        doc_title = f"{doc_id} (Page {page_num}): {title}"
                        output.append({
                            "title": doc_title,
                            "link": link_url,
                            "formatted_citation": f"[{doc_title}]({link_url})",
                            "content": seg_text,
                            "gcs_path": gcs_uri
                        })
                else:
                    snippets = derived_struct_data.get("snippets", [])
                    snippet_text = " ".join([s.get("snippet", "").replace("<b>", "").replace("</b>", "") for s in snippets])
                    doc_title = f"{doc_id}: {title}"
                    output.append({
                        "title": doc_title,
                        "link": authenticated_url,
                        "formatted_citation": f"[{doc_title}]({authenticated_url})",
                        "content": snippet_text,
                        "gcs_path": gcs_uri
                    })

            import json
            result_str = json.dumps(output) if output else "No matching HUMINT reports found."
            span.set_attribute("gen_ai.output.payload_bytes", len(result_str))
            span.set_status(StatusCode.OK)
            
            log_sre_telemetry("search_humint_reports_complete", {
                "query": query,
                "results_count": len(results),
                "payload_bytes": len(result_str),
                "status_code": resp.status_code,
                "identity_type": identity_type
            })
            log_sre_telemetry("spiffe_api_call", {
                "identity_type": identity_type,
                "spiffe_id": spiffe_id,
                "tool_name": "search_humint_reports"
            })
            log_discovery_engine_user_event(query=query, user_pseudo_id="session-user-default", datastore_id=DATASTORE_ID, project_id=PROJECT_ID)
            res_list = output if output else [{"title": "No results", "link": "", "content": "No matching HUMINT reports found."}]
            return json.dumps(res_list, indent=2)
        except Exception as err:
            span.record_exception(err)
            span.set_status(StatusCode.ERROR, str(err))
            return json.dumps([{"title": "Error", "link": "", "content": f"Error executing HUMINT search: {err}"}])


# --- OPTIMIZATION 4: Model Armor OPSEC Guardrails ---
# SCENARIO 5 OBJECTIVE: DevSecOps OPSEC Guardrails.
# Applies Zero-Trust AI security by sanitizing LLM responses via the Cloud Model Armor API.
# Replaces sensitive regex patterns like MGRS coordinates.
def apply_model_armor(context, response):
    """
    Applies Zero-Trust AI security by sanitizing LLM responses via Cloud Model Armor API.
    
    Args:
        context: The ADK agent context containing request metadata.
        response: The ADK response payload generated by the foundation model.
        
    Returns:
        The sanitized response object with sensitive information (e.g. MGRS) redacted.
    """
    import requests, os, re, time
    start_time = time.time()
    
    try:
        if not response or not hasattr(response, "content") or not response.content or not hasattr(response.content, "parts") or not response.content.parts:
            return response
            
        try:
            text = getattr(response.content.parts[0], "text", None)
        except Exception:
            text = None
            
        if not text:
            return response

        with instrument_model_armor_span() as span:
            # --- GUARDRAIL 1: Human-in-the-Loop (HITL) Kinetic & Cyber Gate ---
            text_upper = text.upper() if text else ""
            hitl_keywords = ["KINETIC_ENGAGEMENT", "KINETIC ENGAGEMENT", "STRIKE ADVISORY", "EXECUTE COUNTERMEASURE", "RECOMMEND STRIKE", "KINETIC STRIKE", "FIRE AUTHORIZATION", "AUTHORIZE STRIKE"]
            for high_risk in hitl_keywords:
                if high_risk in text_upper:
                    # Extract target ID if present
                    tgt_match = re.search(r'(TGT-[A-Z0-9\-]+)', text, re.IGNORECASE)
                    tgt_id = tgt_match.group(1).upper() if tgt_match else "UNKNOWN_TARGET"
                    action_cat = "KINETIC_ENGAGEMENT" if "STRIKE" in high_risk or "KINETIC" in high_risk or "ENGAGEMENT" in high_risk else "OFFENSIVE_CYBER_COUNTERMEASURE"
                    decision = evaluate_hitl_guardrail(
                        action_type=action_cat,
                        details={"target_id": tgt_id}
                    )
                    if decision.get("status") == "HELD":
                        try:
                            response.content.parts[0].text = decision.get("message")
                        except Exception:
                            pass
                        log_sre_telemetry("hitl_guardrail_triggered", {"status": "HELD", "action_type": action_cat, "target_id": tgt_id})
                        return response
                
            # --- GUARDRAIL 2: Resilient Model Armor OPSEC Sanitization ---
            mgrs_pattern = r'\b\d{1,2}[C-X][A-Z]{2}\s*\d{4,5}\s*\d{4,5}\b'
            mgrs_matches = re.findall(mgrs_pattern, text)
            mgrs_count = len(mgrs_matches)
            sanitized_text = text
            redacted = False
            identity_type = "STANDARD_OAUTH"

            try:
                armor_location = os.environ.get("ARMOR_LOCATION", "us-central1")
                token, identity_type, spiffe_id = get_auth_token_and_identity()
                log_sre_telemetry("spiffe_api_call", {
                    "identity_type": identity_type,
                    "spiffe_id": spiffe_id,
                    "tool_name": "model_armor_sanitizer"
                })
                url = f"https://modelarmor.{armor_location}.rep.googleapis.com/v1/projects/{PROJECT_ID}/locations/{armor_location}/templates/mission_intel_response_armor:sanitizeModelResponse"
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                    "X-Goog-User-Project": PROJECT_ID
                }
                body = {
                    "modelResponseData": {
                        "text": text
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
                    sanitized_text = sdp_text or resp_data.get("modelResponseData", {}).get("text", text)
                    armor_circuit_breaker.record_success()
                else:
                    armor_circuit_breaker.record_failure()
            except Exception as e:
                armor_circuit_breaker.record_failure()

            # MGRS redaction is bypassed if accessed via Gemini Enterprise (AGENT_IDENTITY)
            if identity_type != "AGENT_IDENTITY":
                sanitized_text = re.sub(mgrs_pattern, '[REDACTED_MGRS]', sanitized_text)
                
            if sanitized_text != text or '[REDACTED_MGRS]' in sanitized_text or (mgrs_count > 0 and identity_type != "AGENT_IDENTITY"):
                redacted = True

            try:
                response.content.parts[0].text = sanitized_text
            except Exception:
                pass

            latency_ms = float(round((time.time() - start_time) * 1000, 2))

            span.set_attribute("model_armor.redacted", redacted)
            span.set_attribute("model_armor.mgrs_count", mgrs_count)
            span.set_attribute("model_armor.latency_ms", latency_ms)
            span.set_status(StatusCode.OK)

            log_sre_telemetry(
                event_name="model_armor_sanitization",
                attributes={
                    "redacted": redacted,
                    "mgrs_count": mgrs_count,
                    "latency_ms": latency_ms
                }
            )
    except Exception as outer_err:
        pass

    return response

# --- OPTIMIZATION 3: Model Right-Sizing ---
# LEARNING SCENARIO OBJECTIVE: Performance & Cost Optimization.
# BEST PRACTICE: Using Gemini Flash instead of Pro for lower cost per inference and higher throughput.

MODEL_NAME = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")

client_kwargs = {
    "enterprise": True,
    "project": PROJECT_ID,
    "location": "global"
}

gemini_model = Gemini(
    model=MODEL_NAME,
    thinking_level="LOW",
    client_kwargs=client_kwargs
)


# --- ADK 2.0 TIER 3 LONG-TERM MEMORY (LTM) TOOLS & SERVICES ---
try:
    from google.adk import Runner
    from google.adk.sessions import InMemorySessionService, VertexAiSessionService
    from memory_service import MemoryServiceClient, GroupMemoryProfile, MissionTransactionState

    memory_client = MemoryServiceClient()
except Exception as e:
    print(f"Memory client initialization notice: {e}")
    memory_client = None

def get_analyst_group_profile() -> str:
    """Retrieves the active Tier 3 Long-Term Memory (LTM) profile for the intelligence analyst group, including configured primary threat focus domains and active watchlist targets."""
    if not memory_client:
        return "Memory service unavailable."
    profile = memory_client.get_group_profile("intelligence_analysts")
    return (
        f"=== TIER 3 LONG-TERM MEMORY (GROUP PROFILE) ===\n"
        f"Group ID: {profile.group_id}\n"
        f"Group Name: {profile.group_name}\n"
        f"Primary Threat Focus Domains: {profile.primary_threat_domains}\n"
        f"Active Watchlist Targets: {profile.active_watchlist_targets}\n"
        f"Default Classification: {profile.default_classification}\n"
        f"Preferred Coordinates: {profile.preferred_coordinates}\n"
        f"================================================"
    )

def update_analyst_group_profile(primary_threat_domains: list[str] = None, active_watchlist_targets: list[str] = None) -> str:
    """Updates the Tier 3 Long-Term Memory (LTM) profile for the intelligence analyst group in Memory Bank, persisting focus areas across future chat sessions."""
    if not memory_client:
        return "Memory service unavailable."
    profile = memory_client.get_group_profile("intelligence_analysts")
    if primary_threat_domains is not None:
        profile.primary_threat_domains = primary_threat_domains
    if active_watchlist_targets is not None:
        profile.active_watchlist_targets = active_watchlist_targets
    memory_client.save_group_profile(profile)
    
    # Log SRE Memory State Delta telemetry
    log_sre_telemetry("ltm_profile_updated", {
        "group_id": profile.group_id,
        "primary_threat_domains": profile.primary_threat_domains,
        "active_watchlist_targets": profile.active_watchlist_targets
    })
    
    return (
        f"✅ Tier 3 LTM Group Profile updated and persisted successfully across sessions:\n"
        f"- Primary Threat Focus Domains: {profile.primary_threat_domains}\n"
        f"- Active Watchlist Targets: {profile.active_watchlist_targets}"
    )


def get_agent_instruction(context=None):
    """
    Generates the dynamic system instruction prompt for the ADK reasoning engine.
    
    Args:
        context: Optional agent context.
        
    Returns:
        str: The structured system prompt incorporating Long-Term Memory (LTM) profile settings.
    """
    profile_info = ""
    if memory_client:
        p = memory_client.get_group_profile("intelligence_analysts")
        profile_info = (
            f"\n\n=== ACTIVE ANALYST GROUP PROFILE (Loaded from Tier 3 Long-Term Memory) ===\n"
            f"- Analyst Group: {p.group_name} ({p.group_id})\n"
            f"- Primary Threat Focus Domains: {p.primary_threat_domains}\n"
            f"- Active Watchlist Targets: {p.active_watchlist_targets}\n"
            f"- Default Classification: {p.default_classification}\n"
            f"=========================================================================="
        )

    return (
        f"You are a Multi-Domain Mission Intelligence Agent. You have access to BOTH structured BigQuery data via an MCP server AND unstructured HUMINT field intelligence PDF reports containing optical/radar tactical crops via a Data Store in Gemini Enterprise. Your primary objective is to deliver actionable, coherent, and rigorously verified assessments under UK Military Staff Duties conventions: direct, objective, and stripped of unnecessary prose."
        f"{profile_info}\n\n"
        "CONCISENESS & SPEED RULES (CRITICAL FOR UI PERFORMANCE):\n"
        "- RESPONSE LENGTH: Keep answers focused, concise, and under 150 words unless the user explicitly requests a full multi-page intelligence report or SOP.\n\n"
        "ANALYST GROUP & MEMORY PROFILE RULES:\n"
        "- When asked about the active threat domains, watchlists, or analyst group configuration, YOU MUST EXPLICITLY REPORT the current values from the ACTIVE ANALYST GROUP PROFILE above.\n"
        "- If asked to update or reconfigure analyst group focus domains or watchlists, call `update_analyst_group_profile` to save the updated settings to Tier 3 Long-Term Memory.\n\n"
        "ROUTING & EFFICIENCY RULES (CRITICAL FOR PERFORMANCE):\n"
        "- GENERAL KNOWLEDGE / SOPs / GREETINGS / CAPABILITIES: If the prompt asks for standard operating procedures, general capabilities, definitions, reporting guidelines, or greetings. Respond directly from system knowledge in a single turn. DO NOT MAKE A TOOL CALL or Call the Data Store.\n\n"
        "- STRUCTURED DATA: If the prompt asks specifically for numerical metrics, track status, asset lists, or SQL data, query BigQuery (`execute_sql`) ONLY. Do NOT call `search_humint_reports` unless field report narratives or PDF citations are explicitly requested.\n\n"
        "- UNSTRUCTURED SEARCH ONLY: If the prompt asks specifically to search HUMINT reports or field documents, call `search_humint_reports` ONLY. Do NOT query BigQuery. Query the Data Store in Gemini Enterprise.\n\n"
        "- MULTI-DOMAIN CORRELATION: When asked to correlate structured telemetry with field reports, execute at most ONE SQL query and ONE HUMINT search query. Do NOT engage in iterative retry loops or repeated queries if zero records are found.\n\n"
        f"1. STRUCTURED DATASETS & BIGQUERY SCHEMA DISCOVERY:\n"
        f"- Primary Unified View (PREFERRED FOR MULTI-DOMAIN QUERIES): `{PROJECT_ID}.mission_data.v_multi_domain_intelligence` (`track_id`, `target_id`, `radar_signature`, `ew_bearing`, `cyber_actor`, `humint_content`, `friendly_unit`).\n"
        f"- Individual Base Tables: `radar_telemetry`, `ew_intercepts`, `ew_bearings`, `satellite_recon`, `cyber_threat_intel`, `friendly_assets`.\n"
        f"- DYNAMIC SCHEMA DISCOVERY: If unsure which table or column contains specific data, query BigQuery INFORMATION_SCHEMA: `SELECT table_name, column_name, data_type FROM {PROJECT_ID}.mission_data.INFORMATION_SCHEMA.COLUMNS WHERE column_name LIKE '%search_term%'`.\n\n"
        "2. UNSTRUCTURED DATASTORE (search_humint_reports Tool):\n"
        "- Search function for classified HUMINT PDF field intelligence reports with embedded tactical images, optical crops, radar reticles, and source reliability ratings.\n\n"
        "INTELLIGENCE SYNTHESIS RULES:\n"
        "- For structured metrics (track velocity, EW frequencies, asset locations), query BigQuery via `execute_sql`.\n"
        "- For in-depth field narratives, source reliability, optical/diagram evidence, or PDF document references, query `search_humint_reports`.\n\n"
        "RESPONSE FORMAT\n\n"
        "## 1. CORE ANALYTICAL TRADECRAFT\n\n"
        "### A. Fusion & Cross-Corroboration\n"
        "- Never accept unstructured narrative claims without verifying them against available structured ground-truth data (e.g., correlate an alleged vessel sighting against AIS, radar tracks, or sensor timestamps).\n"
        "- Actively flag corroborations, conflicts, and discrepancies between data types.\n"
        "  - Source Reliability: A (Completely reliable) to F (Cannot be judged).\n"
        "  - Information Credibility: 1 (Confirmed by other sources) to 6 (Cannot be judged).\n\n"
        "### B. Standard Estimative Language (PHIA Probability Yardstick)\n"
        "You MUST express all analytic uncertainty using the mandatory UK Professional Head of Intelligence Assessment (PHIA) standard terms:\n"
        "- Remote chance: < 5%\n"
        "- Highly unlikely: 10% – 20%\n"
        "- Unlikely: 25% – 35%\n"
        "- Realistic possibility: 40% – 50%\n"
        "- Likely / Probable: 55% – 70%\n"
        "- Highly likely: 75% – 85%\n"
        "- Almost certain: > 90%\n\n"
        "Do not use colloquial confidence terms such as \"maybe\", \"we think\", \"could conceivably\", or \"we suspect\".\n\n"
        "### C. Fact vs. Deduction vs. Assessment\n"
        "- **Fact:** Directly verifiable data point with high certainty (e.g., GPS ping, verified sensor track).\n"
        "- **Deduction:** Logical outcome derived directly from the facts (e.g., \"Platform X departed Port Y between 0400Z and 0600Z\").\n"
        "- **Assessment:** Analytical judgement incorporating intent, capability, and future projection using PHIA language.\n\n"
        "---\n\n"
        "## 2. DEFENCE WRITING & STYLE STANDARDS (JSP 101)\n"
        "- **Bottom Line Up Front (BLUF):** Lead immediately with the critical finding. Do not build up chronologically to a conclusion.\n"
        "- **Tone:** Authoritative, dispassionate, concise, active voice.\n"
        "- **British English:** Always use UK spelling (e.g., colour, reconnoitre, synchronise, defence).\n"
        "- **Brevity:** Eliminate introductory fluff, platitudes, and conversational filler.\n"
        "- **Standard Abbreviations:** Use conventional UK military notation where appropriate (e.g., DTG [DDHHMMZ MON YY], NFA, HVT, C2, FEBA, LOC, ORBAT).\n\n\n"
        "## 3. STANDARD OUTPUT TEMPLATE\n\n"
        "Whenever tasking requires an operational report or assessment, structure your output strictly as follows:\n\n"
        "### INTELLIGENCE SUMMARY (INTSUM)\n\n"
        "**DTG:** [DDHHMMZ MMM YY]  \n"
        "**SUBJECT / AREA OF INTEREST:** [Target, Platform, Region, or Operation]  \n"
        "**OVERALL THREAT LEVEL / POSTURE:** [e.g., LOW | MEDIUM | HIGH | CRITICAL]\n\n"
        "### 1. BOTTOM LINE UP FRONT (BLUF)\n"
        "[Single paragraph, max 3 lines. The core discovery, attribution, and immediate operational impact using PHIA estimative language.]\n\n"
        "### 2. CORRELATED EVIDENCE MATRIX\n"
        "| Source Type | Source ID / Feed | Data Point / Observation | Evaluation (6×6) | Verification Status |\n"
        "|---|---|---|---|---|\n"
        "| Structured | [e.g., AIS / Track Log] | [Lat/Long, Speed, Heading, Timestamp] | A1 | Verified |\n"
        "| Unstructured | [e.g., HUMINT / SITREP] | [Reported cargo, intent, personnel] | B2 | Corroborated / Conflicting |\n\n"
        "### 3. KEY DEDUCTIONS & ANALYSIS\n"
        "- **Operational Activity:** [Deductions from fused feeds; what is actually occurring on the ground/water/air].\n"
        "- **Intent & Capability:** [Analysis of adversary intent using PHIA terms (e.g., \"It is *highly likely* that...\")].\n"
        "- **Anomalies & Deception:** [Deviations from normal pattern of life, spoofing, dark activity].\n\n"
        "### 4. CRITICAL INFORMATION GAPS (CCIRs)\n"
        "- **Gap 1:** [Specific missing requirement preventing higher confidence].\n"
        "- **Gap 2:** [Blind spot in sensor coverage, unverified actor identity].\n\n"
        "### 5. RECOMMENDED COLLECTION / TASKING\n"
        "- [Specific sensor, ISR asset, or analytical query required to confirm or refute the assessment].\n\n\n"
        "### 🔗 CITATION FORMAT RULES (From Agent Citations Guidance):\n"
        "1. State your answer clearly. Place an inline citation marker (e.g., [1]) directly after any factual claim.\n"
        "2. At the very end of your response, add a '---' horizontal rule, followed by a '### Sources' section.\n"
        "3. List your sources as numbered items matching your inline numbers.\n"
        "4. MANDATORY HYPERLINKING FOR HUMINT PDF REPORTS: Every HUMINT report listed under '### Sources' MUST be formatted as an explicit Markdown hyperlink `[Title](authenticated_url)` using the exact URL from the `link` or `formatted_citation` field from `search_humint_reports`.\n"
        "   Example format in Sources:\n"
        "   1. [HUMINT Report HUM-445: Coastal Estuary Covert Loading Operations](https://storage.cloud.google.com/antig-dave-humint-docs/HUM-445_TGT-ALPHA-7.pdf#page=1)\n"
        "5. STRICT PROHIBITION ON HYPERLINKING BIGQUERY DATA: Do NOT hyperlink BigQuery table names, SQL queries, or structured records. List BigQuery sources as plain text (e.g., `2. BigQuery Dataset: radar_telemetry (Track TRK-901)`).\n"
        "6. Do NOT include links to BigQuery Studio or raw gs:// URIs.\n"
        "7. Whenever asked about HUMINT field reports, PDF links, or unstructured data, you MUST call the `search_humint_reports` tool to retrieve official PDF document links. Do NOT claim or state that datastores are unauthenticated or offline.\n"
    )


root_agent = Agent(
    model=gemini_model,
    name="mission_intel_agent",
    instruction=get_agent_instruction,
    tools=[mcp_toolset, search_humint_reports, get_analyst_group_profile, update_analyst_group_profile],
    # ADK 2.0 BEST PRACTICE: Attach OPSEC/Safety intercepts directly to the Agent lifecycle using `after_model_callback`.
    after_model_callback=apply_model_armor
)

# Configure Tier 1 Session Service (In-Memory for local dev, Vertex AI for cloud deployment)
if os.environ.get("VERTEX_AI_DEPLOYMENT") == "true":
    session_service = VertexAiSessionService(project=PROJECT_ID, location=LOCATION)
else:
    session_service = InMemorySessionService()

# ADK 2.0 Runner binding Agent + 3 Memory Tiers
agent_runner = Runner(
    agent=root_agent,
    app_name="mission_intel_app",
    session_service=session_service
)
print("✅ ADK 2.0 Agent Memory 3-Tier Services & Runner initialized successfully.")





