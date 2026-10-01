import os
import json
import sys
import requests
import subprocess
from google.oauth2.credentials import Credentials
from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini

REASONING_ENGINE_ID = "1626863242980622336"
PROJECT_ID = os.environ.get("PROJECT_ID", "284046449012")
LOCATION = os.environ.get("LOCATION", "us-central1")
MODEL_NAME = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")

# In-memory cached token
_CACHED_TOKEN = None

def get_oauth_token() -> str:
    """Retrieves and caches OAuth access token using in-memory token reuse."""
    global _CACHED_TOKEN
    if _CACHED_TOKEN:
        return _CACHED_TOKEN
    try:
        import google.auth
        from google.auth.transport.requests import Request
        creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        if not creds.valid:
            creds.refresh(Request())
        _CACHED_TOKEN = creds.token
        return _CACHED_TOKEN
    except Exception:
        # Fallback to gcloud print-access-token if ADC credentials file needs refresh
        _CACHED_TOKEN = subprocess.check_output(['gcloud', 'auth', 'print-access-token'], stderr=subprocess.DEVNULL).decode('utf-8').strip()
        return _CACHED_TOKEN

# SCENARIO 7 OBJECTIVE: A2A JSON-RPC Protocol over Agent Gateway Transport.
# The Partner Agent invokes the Host Agent securely across domain boundaries via Agent Gateway / Reasoning Engine endpoint.
def query_learning_lab_agent_via_a2a(prompt: str) -> str:
    """
    Sends an Agent-to-Agent (A2A) protocol JSON-RPC request to the Mission Intel Host Agent across domain boundaries.
    
    Args:
        prompt: Tactical intelligence query string (e.g. 'Request threat assessment for TGT-ALPHA-7').
    Returns:
        Sanitized A2A intelligence report response from Mission Intel Host Agent.
    """
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from a2a_protocol import format_a2a_request

    # Construct A2A protocol JSON-RPC payload
    a2a_request_payload = format_a2a_request(
        prompt=prompt,
        caller_identity="NATO-MARCOM-01",
        classification_tag="Demonstrator // REL TO NATO"
    )

    print(f"\n📡 [A2A Protocol Outbound Request from NATO Agent]:")
    print(a2a_request_payload)
    print("----------------------------------------------------------------------")

    # Mode 1: Attempt HTTPS POST across the wire to production Reasoning Engine
    use_remote = os.environ.get("USE_REMOTE_A2A", "true").lower() in ("true", "1", "yes")
    if use_remote:
        try:
            token = get_oauth_token()
            url = f"https://{LOCATION}-aiplatform.googleapis.com/v1/projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{REASONING_ENGINE_ID}:streamQuery"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            body = {
                "input": {
                    "prompt": f"A2A_QUERY: {a2a_request_payload}"
                }
            }
            response = requests.post(url, headers=headers, json=body, timeout=30)
            if response.status_code == 200:
                print(f"\n📥 [A2A HTTPS Response via Agent Gateway / Reasoning Engine]:")
                res_text = response.text
                print(res_text[:500] + ("..." if len(res_text) > 500 else ""))
                print("----------------------------------------------------------------------\n")
                return res_text
            else:
                print(f"⚠️ Remote A2A call failed with HTTP {response.status_code}: {response.text}. Falling back to local handler.")
        except Exception as e:
            print(f"⚠️ Remote A2A HTTP transport error: {e}. Falling back to local handler.")

    # Mode 2: Local fallback execution handler
    from my_host_agent.agent import process_a2a_inbound_query
    a2a_response_payload = process_a2a_inbound_query(a2a_request_payload)

    print(f"\n📥 [A2A Protocol Inbound Local Response from Mission Intel Host Agent]:")
    print(a2a_response_payload)
    print("----------------------------------------------------------------------\n")

    response_data = json.loads(a2a_response_payload)
    return response_data.get("result", {}).get("response", "Error processing A2A query.")

# 2. Configure Gemini LLM with enterprise=True and global location
token = get_oauth_token()
credentials = Credentials(token=token)

client_kwargs = {
    "enterprise": True,
    "project": PROJECT_ID,
    "location": "global",
    "credentials": credentials
}

gemini_model = Gemini(
    model=MODEL_NAME,
    client_kwargs=client_kwargs
)

# 3. Define NATO Coalition Partner Agent
root_agent = Agent(
    model=gemini_model,
    name="nato_marcom_coalition_agent",
    instruction=(
        "You are the NATO Allied Maritime Command (MARCOM) Coalition Partner Agent.\n"
        "You do NOT have direct access to Mission Intel BigQuery databases or internal mission infrastructure.\n\n"
        "INSTRUCTIONS:\n"
        "- When asked about maritime threats, radar tracks, or multi-domain telemetry in the North Sea sector, "
        "use `query_learning_lab_agent_via_a2a` to request intelligence via Agent-to-Agent (A2A) protocol.\n"
        "- Synthesize the sanitized A2A response for coalition command officers."
    ),
    tools=[query_learning_lab_agent_via_a2a]
)

# 4. CLI Entrypoint
if __name__ == "__main__":
    test_prompt = "Request current threat assessment and EW telemetry for target TGT-ALPHA-7 in North Sea."
    print("======================================================================")
    print("🤝 SCENARIO 7: ADK Agent-to-Agent (A2A) Protocol Coalition Demonstration")
    print("======================================================================")
    print(f"NATO Agent Query: {test_prompt}\n")
    
    res = query_learning_lab_agent_via_a2a(test_prompt)
    print(f"Final Coalition Result:\n{res[:500]}")
