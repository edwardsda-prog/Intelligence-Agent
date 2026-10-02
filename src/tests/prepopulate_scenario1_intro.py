#!/usr/bin/env python3
"""
Prepopulate Scenario 1: Introduction (End User Persona)
Sends multi-domain reasoning, memory, and standard RAG queries to the agent.
"""

import sys
import time
import requests
import subprocess

REASONING_ENGINE_RESOURCE = "projects/284046449012/locations/us-central1/reasoningEngines/1314153339948105728"
ENDPOINT_URL = f"https://us-central1-aiplatform.googleapis.com/v1/{REASONING_ENGINE_RESOURCE}:query"

TEST_PROMPTS = [
    {
        "category": "MULTI_DOMAIN",
        "description": "Structured & Unstructured Correlation",
        "prompt": "Cross-reference the radar telemetry for track TRK-901 and track TRK-552 with the intelligence in HUM-448 and evaluate if they represent a coordinated movement."
    },
    {
        "category": "MEMORY",
        "description": "Follow-up Query",
        "prompt": "What are the specific emitter types and tactical call signs for the targets we just discussed?"
    },
    {
        "category": "CITATION",
        "description": "RAG Source Validation",
        "prompt": "Summarize the latest intelligence report for HUM-448 and provide the exact source document link."
    }
]

def get_bearer_token() -> str:
    try:
        token = subprocess.check_output(['gcloud', 'auth', 'print-access-token'], stderr=subprocess.DEVNULL).decode('utf-8').strip()
        if token:
            return token
    except Exception as e:
        print(f"Error fetching gcloud token: {e}")
    sys.exit(1)

def run_test_suite(iterations: int = 1):
    print("======================================================================")
    print("🚀 Prepopulating Scenario 1: Introduction")
    print(f"Iterations: {iterations} | Total Requests: {len(TEST_PROMPTS) * iterations}")
    print("======================================================================")

    results = []

    for iteration in range(1, iterations + 1):
        for idx, test_item in enumerate(TEST_PROMPTS, 1):
            token = get_bearer_token()
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            category = test_item["category"]
            desc = test_item["description"]
            prompt = test_item["prompt"]

            print(f"\n[{idx}/{len(TEST_PROMPTS)}] Iteration {iteration} - {desc} ({category})")
            
            payload = {
                "class_method": "stream_query",
                "input": {
                    "message": prompt,
                    "user_id": f"prepopulate-scen1-iter{iteration}-{idx}"
                }
            }

            start_t = time.time()
            status_code = None
            try:
                res = requests.post(ENDPOINT_URL, headers=headers, json=payload, timeout=120)
                status_code = res.status_code
            except Exception as e:
                status_code = 500

            elapsed_ms = round((time.time() - start_t) * 1000, 2)
            print(f"  Status: {status_code} | Latency: {elapsed_ms} ms")
            results.append({"status_code": status_code, "category": category})
            time.sleep(1)

    successful = sum(1 for r in results if r["status_code"] == 200)
    print(f"\nSummary: {successful}/{len(results)} Success")
    return successful == len(results)

if __name__ == "__main__":
    sys.exit(0 if run_test_suite() else 1)
