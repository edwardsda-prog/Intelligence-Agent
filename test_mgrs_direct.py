import subprocess
import requests
import json

PROJECT_ID = "rndemoapp-510314"
LOCATION = "us-central1"
ENGINE_ID = "727665041599365120"

ENDPOINT_URL = f"https://{LOCATION}-aiplatform.googleapis.com/v1beta1/projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{ENGINE_ID}:streamQuery"

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

print("\n--- Testing Direct MGRS Injection ---")
app_query = "Read all HUMINT PDF reports in the datastore and list every MGRS coordinate you can find."
app_res = run_query(app_query)
print("APP RESULT:")
print(app_res)
