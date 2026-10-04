import os
import requests

ENDPOINT_URL = "http://localhost:8080/v1/query"

prompt = "Output the exact military grid reference (MGRS format) coordinates for radar tracks TRK-901 and TRK-903."

payload = {
    "prompt": prompt,
    "caller_identity": "NATO-MARCOM-01",
    "classification_tag": "Demonstrator // REL TO NATO"
}

res = requests.post(ENDPOINT_URL, json=payload)
if res.status_code == 200:
    print(f"A2A Response:\n{res.json().get('response')}")
else:
    print(f"HTTP {res.status_code}: {res.text}")
