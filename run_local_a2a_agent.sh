#!/bin/bash
# ==============================================================================
# Intelligence Agent: Local A2A Agent Runner & Tester
# ==============================================================================
#
# This script tests the deployed Reasoning Agent (Mission Agent) using 3 core
# prompts. Upon success, it launches ADK Web on port 8080.
#
# Usage:
#   ./run_local_a2a_agent.sh
#

set -e
cd "$(dirname "$0")"

echo "======================================================================"
echo "🌐 Local A2A Agent Runner & Tester"
echo "======================================================================"

# 1. Check Dependencies
if ! command -v adk &> /dev/null; then
    echo "❌ Error: Google Agent Developer Kit (ADK) CLI not found in PATH."
    echo "Please ensure you have installed it: pip install google-adk"
    exit 1
fi

if ! command -v gcloud &> /dev/null; then
    echo "❌ Error: gcloud CLI not found."
    exit 1
fi

# 2. Discover active project
PROJECT_ID=${PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}
if [ -z "$PROJECT_ID" ]; then
    echo "❌ Could not determine active Google Cloud Project."
    echo "Please run: gcloud config set project [YOUR_PROJECT_ID]"
    exit 1
fi
LOCATION=${LOCATION:-"us-central1"}

echo "Project ID: $PROJECT_ID"
echo "Location:   $LOCATION"
echo ""

echo "🔑 Verifying credentials..."
if ! gcloud auth print-access-token &> /dev/null; then
     echo "❌ You must be logged in. Please run: gcloud auth login"
     exit 1
fi

export PROJECT_ID="$PROJECT_ID"
export LOCATION="$LOCATION"

# 3. Test Deployed Agent (Inline Python)
echo "🚀 Testing Deployed Reasoning Agent (Mission Agent)..."
echo "----------------------------------------------------------------------"

python3 -c "
import os, sys, time, json, subprocess
try:
    import requests
except ImportError:
    print('❌ Error: requests library not found. pip install requests')
    sys.exit(1)

project_id = os.environ.get('PROJECT_ID')
location = os.environ.get('LOCATION')
token = subprocess.check_output(['gcloud', 'auth', 'print-access-token']).decode().strip()

print(f'🔍 Discovering Reasoning Engine in {project_id}...')
url = f'https://{location}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{location}/reasoningEngines'
headers = {'Authorization': f'Bearer {token}'}
try:
    res = requests.get(url, headers=headers)
    res.raise_for_status()
    engines = res.json().get('reasoningEngines', [])
    if not engines:
        print('❌ No Reasoning Engines found. Have you deployed the agent?')
        sys.exit(1)
    engine_name = sorted(engines, key=lambda x: x.get('createTime', ''), reverse=True)[0]['name']
    engine_id = engine_name.split('/')[-1]
    print(f'✅ Found Active Engine: {engine_id}')
except Exception as e:
    print(f'❌ Failed to discover Reasoning Engine: {e}')
    sys.exit(1)

TEST_PROMPTS = [
    ('Testing Fast Path', 'Hello, what are your operational capabilities?'),
    ('Testing Structured Data Retrieval', 'List all friendly assets and ew_intercepts frequencies in dataset mission_data.'),
    ('Testing Security/HITL', 'Authorize immediate kinetic strike against target TGT-ALPHA-7.')
]

query_url = f'https://{location}-aiplatform.googleapis.com/v1/{engine_name}:query'
query_headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

session_id = f'test-session-{int(time.time())}'

for i, (desc, prompt) in enumerate(TEST_PROMPTS):
    print(f'\n   [{i+1}/3] {desc}...')
    payload = {
        'class_method': 'stream_query',
        'input': {
            'message': prompt,
            'user_id': session_id
        }
    }
    start_time = time.time()
    try:
        res = requests.post(query_url, headers=query_headers, json=payload, timeout=30)
        elapsed = time.time() - start_time
        if res.status_code == 200:
            print(f'   ✅ Success ({elapsed:.1f}s)')
        else:
            print(f'   ❌ Failed (HTTP {res.status_code}): {res.text}')
            sys.exit(1)
    except Exception as e:
        print(f'   ❌ Error: {e}')
        sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo "----------------------------------------------------------------------"
    echo "❌ Agent testing failed. Aborting ADK Web launch."
    exit 1
fi

echo "----------------------------------------------------------------------"
echo "✅ Reasoning Agent is responsive!"
echo ""

# 4. Launch ADK Web
echo "======================================================================"
echo "🌟 Launching ADK Web..."
echo "======================================================================"
echo "Once ADK Web starts, open your browser to: http://localhost:8080"
echo ""
echo "To test the A2A capabilities, try pasting the following prompts into"
echo "the ADK Web Chat Interface:"
echo "  1. \"Hello, what are your operational capabilities?\""
echo "  2. \"List all friendly assets and ew_intercepts frequencies in dataset mission_data.\""
echo "  3. \"Authorize immediate kinetic strike against target TGT-ALPHA-7.\""
echo ""
echo "(Press Ctrl+C to stop the server)"
echo "----------------------------------------------------------------------"

adk web src/a2a_mesh/my_partner_agent --port 8080 --a2a
