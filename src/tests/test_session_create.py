import subprocess
import requests
import time
import asyncio
import google.auth
import google.oauth2.credentials
from google.adk.sessions.vertex_ai_session_service import VertexAiSessionService

def get_auth_token():
    return subprocess.check_output(['gcloud', 'auth', 'print-access-token']).decode().strip()

token = get_auth_token()
project_id = "antig-dave"
location = "us-central1"
re_id = "1553601408832372736"

# Create Session
session_id = f"test-session-{int(time.time())}"
print(f"Creating session: {session_id}")
original_default = google.auth.default
google.auth.default = lambda *args, **kwargs: (google.oauth2.credentials.Credentials(token), project_id)

try:
    srv = VertexAiSessionService(project=project_id, location=location, agent_engine_id=re_id)
    asyncio.run(srv.create_session(app_name="mission_intel_app", user_id="e2e_test_runner", session_id=session_id))
    print("Session created successfully.")
except Exception as e:
    print(f"Create session error: {e}")

google.auth.default = original_default

url = f"https://{location}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{location}/reasoningEngines/{re_id}:streamQuery"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
}
body = {
    "class_method": "stream_query",
    "input": {
        "message": "Hello, what are your operational capabilities?",
        "user_id": "e2e_test_runner",
        "session_id": session_id
    }
}

print(f"Querying with session_id")
resp = requests.post(url, headers=headers, json=body)
print(f"Status Code: {resp.status_code}")
if resp.status_code != 200:
    print(resp.text)
else:
    for line in resp.iter_lines():
        if line:
            print(line.decode("utf-8"))

