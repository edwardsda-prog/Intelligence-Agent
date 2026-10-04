import os
import requests
import subprocess
import json

PROJECT_ID = "rndemoapp-510314"
LOCATION = "us-central1"

def get_engine_id():
    # Use gcloud curl to call reasoningEngines API
    token = subprocess.check_output(['gcloud', 'auth', 'print-access-token']).decode('utf-8').strip()
    url = f"https://{LOCATION}-aiplatform.googleapis.com/v1beta1/projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines"
    headers = {"Authorization": f"Bearer {token}"}
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        engines = res.json().get('reasoningEngines', [])
        if engines:
            # Sort by updateTime
            engines.sort(key=lambda x: x.get('updateTime', ''), reverse=True)
            return engines[0]['name'].split('/')[-1]
    return None

engine_id = get_engine_id()
if not engine_id:
    print("Could not find deployed Reasoning Engine.")
    exit(1)

print(f"Using Reasoning Engine ID: {engine_id}")
ENDPOINT_URL = f"https://{LOCATION}-aiplatform.googleapis.com/v1beta1/projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{engine_id}:streamQuery"

token = subprocess.check_output(['gcloud', 'auth', 'print-access-token']).decode('utf-8').strip()
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

def run_query(prompt):
    payload = {
        "class_method": "stream_query",
        "input": {
            "message": prompt,
            "user_id": "test-mgrs"
        }
    }

    res = requests.post(ENDPOINT_URL, headers=headers, json=payload, stream=True)
    chunks = []
    if res.status_code == 200:
        for line in res.iter_lines():
            if not line:
                continue
            line_str = line.decode("utf-8", errors="replace")
            if line_str.startswith("data: "):
                line_str = line_str[6:]
            try:
                event = json.loads(line_str)
                if "content" in event and isinstance(event["content"], str):
                    chunks.append(event["content"])
                elif "content" in event and isinstance(event["content"], dict):
                    parts = event["content"].get("parts", [])
                    for p in parts:
                        if "text" in p:
                            chunks.append(p["text"])
                elif "error_message" in event:
                    chunks.append(f"Error: {event['error_message']}")
            except Exception:
                pass
        return "".join(chunks) if chunks else res.text
    else:
        return f"HTTP {res.status_code}: {res.text}"

print("\n--- Testing Standard Gemini Enterprise App Query ---")
app_query = "Output the exact military grid reference (MGRS format) coordinates for radar tracks TRK-901 and TRK-903."
app_res = run_query(app_query)
print("APP RESULT:")
print(app_res)

print("\n--- Testing NATO Partner Agent (A2A) Query ---")
a2a_query = "A2A_QUERY: Output the exact military grid reference (MGRS format) coordinates for radar tracks TRK-901 and TRK-903."
a2a_res = run_query(a2a_query)
print("A2A RESULT:")
print(a2a_res)
