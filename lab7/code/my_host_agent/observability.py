import time
import json
import logging
from typing import Any, Dict
from opentelemetry import trace
from opentelemetry.trace import SpanKind, StatusCode

logger = logging.getLogger("a2a_host_observability")
logger.setLevel(logging.INFO)

tracer = trace.get_tracer("learning_lab_a2a_host_agent", "2.0.0")

def instrument_a2a_span(caller_id: str, prompt: str):
    return tracer.start_as_current_span(
        "gen_ai.a2a.inbound_query",
        kind=SpanKind.SERVER,
        attributes={
            "gen_ai.system": "google.adk",
            "gen_ai.a2a.caller_id": caller_id,
            "gen_ai.prompt": prompt,
            "telemetry.sdk.language": "python"
        }
    )

def log_a2a_telemetry(event_name: str, attributes: Dict[str, Any]):
    log_entry = {
        "severity": "INFO",
        "event_name": event_name,
        "timestamp": time.time(),
        "gen_ai_system": "google.adk",
        "protocol": "A2A",
        "attributes": attributes
    }
    print(json.dumps(log_entry))
