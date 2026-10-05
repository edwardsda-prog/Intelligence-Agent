#!/usr/bin/env python3
"""
Prepopulate Scenario 4: Memory Architecture (Operator Persona)
Sends memory-related test prompts to the deployed Vertex AI Reasoning Engine instance
to generate live metrics for the Memory dashboard (State Deltas, LTM Fetches).
"""

import sys
import time
import requests
import subprocess
import uuid

REASONING_ENGINE_RESOURCE = "projects/284046449012/locations/us-central1/reasoningEngines/1314153339948105728"
ENDPOINT_URL = f"https://us-central1-aiplatform.googleapis.com/v1/{REASONING_ENGINE_RESOURCE}:query"

TEST_PROMPTS = [
    {
        "category": "LTM_FETCH",
        "description": "Trigger Tier 3 Profile Load",
        "prompt": "Review the intelligence_analysts group memory profile. What are the primary threat domains we are tracking?"
    },
    {
        "category": "TIER_2_MUTATION",
        "description": "Trigger Tier 2 Blackboard State Update",
        "prompt": "I found a new threat group called KINETIC-VANGUARD. Add this to your temporary blackboard state."
    },
    {
        "category": "LTM_MUTATION",
        "description": "Trigger Tier 3 Profile Update",
        "prompt": "Permanently update the intelligence_analysts group memory profile to include KINETIC-VANGUARD in the primary threat domains."
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
    print("🚀 Prepopulating Scenario 4: Agent Memory Architecture")
    print(f"Iterations: {iterations} | Total Requests: {len(TEST_PROMPTS) * iterations}")
    print("======================================================================")

    session_id = f"test-memory-{uuid.uuid4().hex[:8]}"

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

            print(f"[{idx}/{len(TEST_PROMPTS)}] 📨 [{category}] {desc}")

            payload = {
                "input": {"prompt": prompt, "session_id": session_id}
            }

            try:
                start_time = time.time()
                response = requests.post(ENDPOINT_URL, headers=headers, json=payload, timeout=60)
                latency = round(time.time() - start_time, 2)

                if response.status_code == 200:
                    resp_json = response.json()
                    output_text = resp_json.get("output", "No Output")
                    print(f"   ✅ SUCCESS ({latency}s)")
                else:
                    print(f"   ❌ FAILED HTTP {response.status_code} ({latency}s)")
                    print(f"   Details: {response.text[:200]}")
            except Exception as e:
                print(f"   ❌ EXCEPTION: {e}")

            time.sleep(2)

    print("✅ Prepopulation for Scenario 4 Complete.")

if __name__ == "__main__":
    run_test_suite()
