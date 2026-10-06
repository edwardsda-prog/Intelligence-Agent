import time
import json
import logging
from typing import Any, Dict
from opentelemetry import trace
from opentelemetry.trace import SpanKind, Status, StatusCode

logger = logging.getLogger("mission_intel_observability")
logger.setLevel(logging.INFO)

tracer = trace.get_tracer("mission_intel_agent", "2.0.0")

def instrument_tool_span(tool_name: str, query: str, conversation_id: str = "default_session"):
    """
    Context manager / helper to create OpenTelemetry spans adhering to OpenTelemetry GenAI Semantic Conventions.
    """
    return tracer.start_as_current_span(
        f"gen_ai.tool.{tool_name}",
        kind=SpanKind.CLIENT,
        attributes={
            "gen_ai.system": "google.adk",
            "gen_ai.tool.name": tool_name,
            "gen_ai.conversation.id": conversation_id,
            "gen_ai.prompt": query,
            "telemetry.sdk.language": "python",
            "telemetry.sdk.name": "opentelemetry"
        }
    )

def instrument_model_armor_span(conversation_id: str = "default_session"):
    """
    Context manager / helper to create OpenTelemetry spans for Model Armor callback execution.
    """
    return tracer.start_as_current_span(
        "gen_ai.callback.model_armor",
        kind=SpanKind.INTERNAL,
        attributes={
            "gen_ai.system": "google.adk",
            "gen_ai.conversation.id": conversation_id,
            "security.component": "model_armor",
            "telemetry.sdk.language": "python",
            "telemetry.sdk.name": "opentelemetry"
        }
    )

def log_sre_telemetry(event_name: str, attributes: Dict[str, Any]):
    """
    Emits structured JSON logs to stdout for seamless Cloud Logging ProtoPayload / JSON extraction.
    """
    log_entry = {
        "severity": "INFO",
        "event_name": event_name,
        "timestamp": time.time(),
        "gen_ai_system": "google.adk",
        "attributes": attributes
    }
    print(json.dumps(log_entry))

def log_discovery_engine_user_event(query: str, user_pseudo_id: str = "session-user-default", datastore_id: str = "humint-pdf-datastore-1790507563", project_id: str = None) -> bool:
    """
    Pushes structured UserEvent JSON payloads to Google Cloud Discovery Engine API
    to populate Gemini Enterprise Business / Adoption Analytics dashboard.
    """
    try:
        import requests
        import google.auth
        import google.auth.transport.requests

        if not project_id:
            _, project_id = google.auth.default()

        creds, _ = google.auth.default()
        req = google.auth.transport.requests.Request()
        creds.refresh(req)

        headers = {
            "Authorization": f"Bearer {creds.token}",
            "X-Goog-User-Project": project_id,
            "Content-Type": "application/json"
        }

        url = f"https://discoveryengine.googleapis.com/v1alpha/projects/{project_id}/locations/global/collections/default_collection/dataStores/{datastore_id}/userEvents:write"
        payload = {
            "eventType": "search",
            "userPseudoId": user_pseudo_id,
            "searchInfo": {
                "searchQuery": query
            }
        }
        res = requests.post(url, headers=headers, json=payload, timeout=3)
        return res.status_code == 200
    except Exception as e:
        logger.warning(f"Business Analytics UserEvent push notice: {e}")
        return False

def instrument_memory_span(memory_tier: str, action: str, conversation_id: str = "default_session", group_id: str = "intelligence_analysts"):
    """
    Creates OpenTelemetry span for ADK 2.0 Agent Memory operations (Tier 1 Working Memory, Tier 2 Blackboard State, Tier 3 LTM Memory Bank).
    """
    return tracer.start_as_current_span(
        f"gen_ai.memory.{memory_tier}.{action}",
        kind=SpanKind.INTERNAL,
        attributes={
            "gen_ai.system": "google.adk",
            "gen_ai.memory.tier": memory_tier,
            "gen_ai.memory.action": action,
            "gen_ai.conversation.id": conversation_id,
            "gen_ai.user.group_id": group_id,
            "telemetry.sdk.language": "python",
            "telemetry.sdk.name": "opentelemetry"
        }
    )

def log_memory_event(event_name: str, group_id: str, state_delta: dict[str, Any], latency_ms: float = None):
    """
    Emits structured state_delta logs to stdout for Cloud Logging and SRE monitoring.
    """
    log_entry = {
        "severity": "INFO",
        "message": "Commit state delta success" if "update" in event_name or "delta" in event_name else event_name,
        "event_name": event_name,
        "group_id": group_id,
        "timestamp": time.time(),
        "gen_ai_system": "google.adk",
        "state_delta": state_delta
    }
    if latency_ms is not None:
        log_entry["latency_ms"] = latency_ms
    print(json.dumps(log_entry))

def log_model_armor_payload(user_prompt: str, sanitized_text: str, pij_match: bool, action_taken: str):
    """
    Writes a custom log to 'model_armor_payload_logger' so that BigQuery Log Sink 
    can correctly route it to the model_armor_logs.model_armor_payload_logger table.
    """
    try:
        from google.cloud import logging as cloud_logging
        from google.cloud.logging.resource import Resource
        import time
        client = cloud_logging.Client()
        logger = client.logger("model_armor_payload_logger")
        
        # Use a generic global resource type to ensure it gets logged.
        res = Resource(type="global", labels={})
        
        payload = {
            "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            "event_name": "model_armor_sanitization",
            "category": "OPSEC",
            "template_id": "mission_intel_response_armor",
            "user_prompt": user_prompt,
            "sanitized_text": sanitized_text,
            "pij_match": pij_match,
            "action_taken": action_taken
        }
        logger.log_struct(payload, resource=res, severity="INFO")
    except Exception as e:
        logger.warning(f"Failed to log model armor payload: {e}")
