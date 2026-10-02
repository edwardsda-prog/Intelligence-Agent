import os, sys, requests, subprocess, json
token = subprocess.check_output(["gcloud", "auth", "print-access-token"], text=True).strip()
re_id = "7800436314989395968"
url = f"https://us-central1-aiplatform.googleapis.com/v1/projects/antig-dave/locations/us-central1/reasoningEngines/{re_id}:query"
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
a2a_payload = {
    "jsonrpc": "2.0",
    "method": "query",
    "params": {
        "prompt": "Request threat assessment for TGT-ALPHA-7 in North Sea.",
        "caller_identity": "NATO-MARCOM-01",
        "classification_tag": "Demonstrator // REL TO NATO"
    },
    "id": "req-nato-live-1"
}
payload = {
    "class_method": "stream_query",
    "input": {
        "message": f"A2A_QUERY: {json.dumps(a2a_payload)}", "user_id": "debugger"
    }
}
res = requests.post(url, headers=headers, json=payload)
print("Status:", res.status_code)
print("Body:", res.text)
