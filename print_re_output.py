import os, sys, requests, subprocess
token = subprocess.check_output(["gcloud", "auth", "print-access-token"], text=True).strip()
re_id = "7800436314989395968"
url = f"https://us-central1-aiplatform.googleapis.com/v1/projects/antig-dave/locations/us-central1/reasoningEngines/{re_id}:streamQuery"
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
payload = {
    "class_method": "stream_query",
    "input": {
        "message": "Use search_humint_reports to search for TGT-ALPHA-7. Return the exact error string you receive.",
        "user_id": "debugger"
    }
}
res = requests.post(url, headers=headers, json=payload)
print(res.text)
