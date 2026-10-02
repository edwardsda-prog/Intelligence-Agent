#!/usr/bin/env python3
"""
Prepopulate FinOps Dashboard Script
Sends a comprehensive suite of high-token test prompts to the deployed Vertex AI Reasoning Engine instance
to generate live OpenTelemetry spans for the FinOps Token Burn dashboard.
"""

import sys
import json
import time
import requests
import subprocess

REASONING_ENGINE_RESOURCE = "projects/284046449012/locations/us-central1/reasoningEngines/1314153339948105728"
ENDPOINT_URL = f"https://us-central1-aiplatform.googleapis.com/v1/{REASONING_ENGINE_RESOURCE}:query"

TEST_PROMPTS = [
    {
        "category": "HIGH_REASONING",
        "description": "Multi-Step Correlation Request",
        "prompt": "Cross-reference the radar telemetry for track TRK-901 and track TRK-552 with the intelligence in HUM-448 and evaluate if they represent a coordinated movement."
    },
    {
        "category": "HIGH_OUTPUT",
        "description": "Large Output Request",
        "prompt": "Provide a comprehensive, detailed, step-by-step summary of all information we have regarding target TGT-ALPHA-7 including its MGRS locations."
    },
    {
        "category": "TOOL_THRASHING",
        "description": "Multi-Tool Request",
        "prompt": "Search BigQuery for all active threat identifiers and then search Discovery Engine for all available intelligence reports on each identifier."
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

def run_test_suite(iterations: int = 5):
    print("======================================================================")
    print("🚀 Prepopulating FinOps Token Burn Dashboard")
    print(f"Target Reasoning Engine: {REASONING_ENGINE_RESOURCE}")
    print(f"Iterations: {iterations} | Total Requests: {len(TEST_PROMPTS) * iterations}")
    print("======================================================================")

    results = []

    for iteration in range(1, iterations + 1):
        print(f"\n--- Starting Iteration {iteration}/{iterations} ---")
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
            print(f"  Prompt: \"{prompt}\"")

            payload = {
                "class_method": "stream_query",
                "input": {
                    "message": prompt,
                    "user_id": f"prepopulate-finops-iter{iteration}-{idx}"
                }
            }

            start_t = time.time()
            status_code = None
            error_msg = None

            try:
                res = requests.post(ENDPOINT_URL, headers=headers, json=payload, timeout=120)
                status_code = res.status_code
                if status_code != 200:
                    error_msg = res.text[:200]
            except Exception as e:
                print(f"  ❌ Exception during call: {e}")
                status_code = 500
                error_msg = str(e)

            elapsed_ms = round((time.time() - start_t) * 1000, 2)
            if status_code == 200:
                print(f"  ✅ Status: 200 | Latency: {elapsed_ms} ms")
            else:
                print(f"  ❌ Status: {status_code} | Latency: {elapsed_ms} ms | Error: {error_msg}")

            results.append({
                "iteration": iteration,
                "index": idx,
                "category": category,
                "description": desc,
                "status_code": status_code,
                "latency_ms": elapsed_ms
            })

            time.sleep(1)

    print("\n======================================================================")
    print("📊 Test Execution Summary")
    print("======================================================================")
    successful = sum(1 for r in results if r["status_code"] == 200)
    print(f"Total Executed: {len(results)}")
    print(f"Successful (HTTP 200): {successful}")
    print(f"Failed: {len(results) - successful}")

    for r in results:
        status_str = "✅ PASS" if r["status_code"] == 200 else f"❌ FAIL ({r['status_code']})"
        print(f"  Iter {r['iteration']} [{r['index']}] {r['category']:<20} | {status_str} | {r['latency_ms']} ms")

    return successful == len(results)

if __name__ == "__main__":
    success = run_test_suite(iterations=5)
    sys.exit(0 if success else 1)
