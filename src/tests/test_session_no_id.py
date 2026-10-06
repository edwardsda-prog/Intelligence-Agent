import subprocess
import requests

def get_auth_token():
    return subprocess.check_output(['gcloud', 'auth', 'print-access-token']).decode().strip()

token = get_auth_token()
project_id = "antig-dave"
location = "us-central1"
re_id = "1553601408832372736"

url = f"https://{location}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{location}/reasoningEngines/{re_id}:streamQuery"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
}

body = {
    "class_method": "stream_query",
    "input": {
        "message": "Hello, what are your operational capabilities?",
        "user_id": "e2e_test_runner"
    }
}

print(f"Testing without session_id")
resp = requests.post(url, headers=headers, json=body)
print(f"Status Code: {resp.status_code}")
if resp.status_code != 200:
    print(resp.text)
else:
    for line in resp.iter_lines():
        if line:
            print(line.decode("utf-8"))

