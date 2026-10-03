#!/usr/bin/env python3
"""
==============================================================================
Intelligence Agent: Scenario Data Generator
==============================================================================

This script is designed to be run immediately before an Ops or Security training
session/demo. It automatically discovers your active Reasoning Engine instance
and simulates a user interacting with it by sending the exact prompts outlined
in the `Trainer_Scenarios.md` document.

This ensures that the Cloud Monitoring Dashboards (Observability, FinOps, Model Armor)
are prepopulated with rich, realistic telemetry data (traces, latencies, PII redactions,
HITL guardrail triggers, and A2A requests) for the demonstrator to highlight.

Usage:
    python3 generate_scenario_data.py
"""

import os
import sys
import json
import time
import subprocess
import requests

SCENARIO_PROMPTS = {
    "Scenario 1: End User (Fast Path, RAG, & SQL)": [
        "Hello, what are your operational capabilities?",
        "List all friendly assets and ew_intercepts frequencies in dataset mission_data.",
        "Find the HUMINT PDF report for target TGT-ALPHA-7 and cross-reference with radar track TRK-901 in BigQuery.",
        "What are the specific emitter types and tactical call signs for the targets we just discussed?",
        "Search unstructured HUMINT reports for optic crops of coastal missile batteries and list the MGRS grid coordinates."
    ],
    "Scenario 3: Security (HITL & NATO A2A)": [
        "Authorize immediate kinetic strike against target TGT-ALPHA-7.",
        "Request maritime threat assessment and electronic warfare telemetry for target TGT-ALPHA-7 on behalf of the NATO MARCOM Task Force."
    ]
}

def get_auth_token():
    """Retrieves GCP access token via gcloud CLI."""
    try:
        return subprocess.check_output(['gcloud', 'auth', 'print-access-token']).decode().strip()
    except Exception as e:
        print(f"❌ Error getting gcloud auth token: {e}")
        sys.exit(1)

def get_default_project():
    """Discovers active gcloud project ID."""
    try:
        return subprocess.check_output(['gcloud', 'config', 'get-value', 'project']).decode().strip()
    except Exception:
        return "antig-dave"

def discover_reasoning_engine(project_id, location, token):
    """Discovers the active Reasoning Engine ID."""
    url = f"https://{location}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{location}/reasoningEngines"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        res = requests.get(url, headers=headers)
        res.raise_for_status()
        engines = res.json().get("reasoningEngines", [])
        if not engines:
            print(f"❌ No Reasoning Engines found in {project_id}. Did you run deploy.sh?")
            sys.exit(1)
        # Get the most recently created engine
        latest_engine = sorted(engines, key=lambda x: x.get('createTime', ''), reverse=True)[0]
        return latest_engine['name']
    except Exception as e:
        print(f"❌ Failed to discover Reasoning Engine in {project_id}: {e}")
        sys.exit(1)

def run_scenarios():
    import argparse
    parser = argparse.ArgumentParser(description="Scenario Telemetry Generator")
    parser.add_argument("--project", help="GCP Project ID", default=get_default_project())
    args = parser.parse_args()

    print("======================================================================")
    print("🚀 INTELLIGENCE AGENT: SCENARIO TELEMETRY GENERATOR")
    print("======================================================================")
    
    project_id = args.project
    location = "us-central1"
    token = get_auth_token()
    
    print(f"🔍 Discovering active Reasoning Engine in {project_id} ({location})...")
    engine_name = discover_reasoning_engine(project_id, location, token)
    engine_id = engine_name.split("/")[-1]
    print(f"✅ Found Active Engine: {engine_id}")
    
    url = f"https://{location}-aiplatform.googleapis.com/v1/{engine_name}:query"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    total_prompts = sum(len(prompts) for prompts in SCENARIO_PROMPTS.values())
    current_prompt = 0
    
    # We use a single session ID for the End User scenario to test memory persistence
    session_id = f"demo-session-{int(time.time())}"

    for scenario_name, prompts in SCENARIO_PROMPTS.items():
        print(f"\n📂 Executing {scenario_name}")
        print("----------------------------------------------------------------------")
        for prompt in prompts:
            current_prompt += 1
            print(f"   [{current_prompt}/{total_prompts}] Sending Prompt: '{prompt[:60]}...'")
            
            payload = {
                "class_method": "stream_query",
                "input": {
                    "message": prompt,
                    "user_id": session_id
                }
            }
            
            start_time = time.time()
            try:
                res = requests.post(url, headers=headers, json=payload, timeout=60)
                elapsed = time.time() - start_time
                if res.status_code == 200:
                    print(f"   ✅ Success ({elapsed:.1f}s)")
                else:
                    print(f"   ⚠️ Warning (HTTP {res.status_code}): {res.text}")
            except Exception as e:
                print(f"   ❌ Error: {e}")
            
            # Add a natural delay to spread out the telemetry over time
            if current_prompt < total_prompts:
                print("   ⏳ Waiting 5 seconds before next prompt to simulate user delay...")
                time.sleep(5)

    print("\n======================================================================")
    print("🎉 SCENARIO DATA GENERATION COMPLETE")
    print("Your Observability, FinOps, and Security Dashboards have been populated!")
    print("======================================================================")

if __name__ == "__main__":
    run_scenarios()
