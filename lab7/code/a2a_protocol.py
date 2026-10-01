import json
import time
from typing import Dict, Any

class AgentCard:
    """
    ADK Agent-to-Agent (A2A) Protocol Agent Card Definition.
    Machine-readable metadata declaring capabilities, supported classification levels, and RPC endpoints.
    """
    def __init__(self, agent_id: str, name: str, classification_levels: list):
        self.agent_id = agent_id
        self.name = name
        self.classification_levels = classification_levels

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "version": "2.0.0",
            "protocol_version": "a2a-v1-jsonrpc",
            "classification_supported": self.classification_levels,
            "capabilities": [
                "multi_domain_telemetry_query",
                "threat_actor_attribution",
                "humint_field_report_search"
            ],
            "auth_methods": ["BearerToken", "AgentGatewayOAuth2"]
        }

def format_a2a_request(prompt: str, caller_identity: str, classification_tag: str = "Demonstrator // REL TO NATO") -> str:
    """Formats an outgoing A2A query request as a JSON-RPC 2.0 payload."""
    payload = {
        "jsonrpc": "2.0",
        "method": "a2a.query",
        "params": {
            "prompt": prompt,
            "caller_identity": caller_identity,
            "classification_tag": classification_tag,
            "timestamp": time.time()
        },
        "id": f"a2a-req-{int(time.time())}"
    }
    return json.dumps(payload)

def format_a2a_response(request_id: str, result_text: str, classification_tag: str = "Demonstrator // REL TO NATO") -> str:
    """Formats an A2A query response as a JSON-RPC 2.0 payload."""
    payload = {
        "jsonrpc": "2.0",
        "result": {
            "response": result_text,
            "classification_tag": classification_tag,
            "sanitized_by_opsec": True
        },
        "id": request_id
    }
    return json.dumps(payload)
