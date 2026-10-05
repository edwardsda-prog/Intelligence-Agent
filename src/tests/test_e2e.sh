#!/bin/bash
# ==============================================================================
# End-to-End Automated Workshop Test Suite: Mission Intel Multi-Domain AI Platform
# ==============================================================================
#
# Supported Execution Modes:
#   1. Fast Hermetic / Mock Mode:
#      ./test_e2e.sh --mock (or --offline)
#
#   2. Unit-Only Gate:
#      ./test_e2e.sh --unit-only
#
#   3. Full Live Cloud Deployment & Validation:
#      ./test_e2e.sh --live (default when run without flags)
# ==============================================================================

# Change to project root so paths execute correctly when run from anywhere
cd "$(dirname "$0")/.."

set -e

if [ -d "/home/aguser/Documents/Research/bin" ]; then
    export PATH="/home/aguser/Documents/Research/bin:$PATH"
fi

MODE="live"
if [[ "$1" == "--mock" || "$1" == "--offline" ]]; then
    MODE="mock"
elif [[ "$1" == "--unit-only" ]]; then
    MODE="unit-only"
elif [[ "$1" == "--live" ]]; then
    MODE="live"
fi

# ------------------------------------------------------------------------------
# UNIT-ONLY MODE
# ------------------------------------------------------------------------------
if [[ "$MODE" == "unit-only" ]]; then
    echo "======================================================================"
    echo "🧪 Running Unit Test Suite Only"
    echo "======================================================================"
    python3 -m unittest discover -s tests -p "test_*.py" -v
    exit $?
fi

# ------------------------------------------------------------------------------
# HERMETIC / MOCK MODE
# ------------------------------------------------------------------------------
if [[ "$MODE" == "mock" ]]; then
    echo "======================================================================"
    echo "⚡ Fast Hermetic / Mock Mode requested"
    echo "======================================================================"
    python3 tests/test_prompts.py --mock
    exit $?
fi

# ------------------------------------------------------------------------------
# LIVE CLOUD MODE: PRE-FLIGHT VALIDATION & UPFRONT UNIT GATE
# ------------------------------------------------------------------------------
echo "======================================================================"
echo "🧪 Running End-to-End Test Suite for Final Unified Agent"
echo "Mode:     LIVE CLOUD VALIDATION"
echo "======================================================================"

export PROJECT_ID=${PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}
export LOCATION=${LOCATION:-"us-central1"}
export TOKEN=$(gcloud auth print-access-token 2>/dev/null || true)

if [ -z "$PROJECT_ID" ]; then
    echo "❌ [PRE-FLIGHT FAILURE] Google Cloud PROJECT_ID is not configured."
    exit 1
fi

if [ -z "$TOKEN" ]; then
    echo "❌ [PRE-FLIGHT FAILURE] Unable to obtain Google Cloud access token."
    exit 1
fi

echo "Project:  $PROJECT_ID"
echo "Location: $LOCATION"
echo "Auth:     Authenticated ✅"

# ------------------------------------------------------------------------------
# PHASE 1: Upfront Fail-Fast Unit Test Gate
# ------------------------------------------------------------------------------
echo ""
echo "=== Phase 1: Upfront Unit Test Gate ==="
python3 -m unittest discover -s tests -p "test_*.py"
echo "✅ Phase 1 Passed: All unit tests verified successfully. Proceeding with cloud provisioning."

# ------------------------------------------------------------------------------
# STEP 0: Provision Unified Environment, Gemini Enterprise & IAM Security
# ------------------------------------------------------------------------------
echo ""
echo "=== STEP 0: Provisioning Unified Environment, Gemini Enterprise & IAM Security ==="
./infrastructure/setup.sh

# ------------------------------------------------------------------------------
# STEP 1: Data Foundations & BigQuery
# ------------------------------------------------------------------------------
echo ""
echo "=== STEP 1: Testing BigQuery Setup ==="
bq query --location=us-central1 --use_legacy_sql=false --project_id="$PROJECT_ID" < infrastructure/schemas/setup_dataset.sql > /dev/null 2>&1
ROW_COUNT=$(bq query --location=us-central1 --use_legacy_sql=false --format=csv "SELECT COUNT(*) FROM \`${PROJECT_ID}.mission_data.radar_telemetry\`" | tail -n 1)
echo "✅ BigQuery dataset created. radar_telemetry row count: $ROW_COUNT (Expected: 8)"

# ------------------------------------------------------------------------------
# STEP 2: Local SQLite DB & Cloud Run MCP
# ------------------------------------------------------------------------------
echo ""
echo "=== STEP 2: Local SQLite & Cloud Run MCP ==="
# python3 lab2/code/setup_local_db.py (deprecated)

echo "Deploying BigQuery MCP Server to Cloud Run..."
gcloud run deploy bigquery-mcp-server --quiet \
  --image us-central1-docker.pkg.dev/database-toolbox/toolbox/toolbox:latest \
  --region "$LOCATION" \
  --project "$PROJECT_ID" \
  --allow-unauthenticated \
  --min-instances=1 \
  --concurrency=80 \
  --set-env-vars BIGQUERY_PROJECT="$PROJECT_ID" \
  --args="--prebuilt","bigquery","--address","0.0.0.0","--port","8080" > /dev/null 2>&1

CLOUD_RUN_URL=$(gcloud run services describe bigquery-mcp-server --region "$LOCATION" --project "$PROJECT_ID" --format="value(status.url)")
echo "✅ Cloud Run MCP Server URL: $CLOUD_RUN_URL"

# ------------------------------------------------------------------------------
# STEP 3: Setup Datastore for Scenario 5 / 8
# ------------------------------------------------------------------------------
echo ""
echo "=== STEP 3: Setup Unstructured Datastore (HUMINT PDFs) ==="
./infrastructure/setup_discovery_engine.sh

# ------------------------------------------------------------------------------
# STEP 4: Setup RAG (Scenario 8)
# ------------------------------------------------------------------------------
echo ""
echo "=== STEP 4: Setup RAG ==="
if [ -f lab8/code/provision_rag.py ]; then
    cd lab8/code
    python3 provision_rag.py
    cd ../..
fi

# ------------------------------------------------------------------------------
# STEP 5: Setup Model Armor (Scenario 4)
# ------------------------------------------------------------------------------
echo ""
echo "=== STEP 5: Setup Model Armor ==="
./infrastructure/security/setup_model_armor.sh

# ------------------------------------------------------------------------------
# STEP 6: Deploy Final Agent
# ------------------------------------------------------------------------------
echo ""
echo "=== STEP 6: Deploying Final Consolidated Agent ==="
./final_agent/deploy.sh
echo "✅ Final Agent deployed."

# Export the AGENT_ENGINE_ID if deploy.sh doesn't export it globally
# We can find it by querying ReasoningEngines or from Discovery Engine agents list
RE_NAME=$(curl -s -H "Authorization: Bearer ${TOKEN}" \
  "https://${LOCATION}-aiplatform.googleapis.com/v1/projects/${PROJECT_ID}/locations/${LOCATION}/reasoningEngines" | \
  python3 -c "import sys, json; data = json.load(sys.stdin); res = (data.get('reasoningEngines') or [{}])[0].get('name', ''); print(res if res else '')")
export AGENT_ENGINE_ID=$(echo "$RE_NAME" | awk -F'/' '{print $NF}')

# ------------------------------------------------------------------------------
# COMPREHENSIVE END-TO-END VALIDATION: Full Cohort 39-Test Verification Suite
# ------------------------------------------------------------------------------
echo ""
echo "=== COMPREHENSIVE END-TO-END VALIDATION: Testing All Prompts in Live Mode ==="
python3 tests/test_prompts.py --live --project="$PROJECT_ID" --location="$LOCATION"

echo ""
echo "======================================================================"
echo "📊 POPULATING OBSERVABILITY & MEMORY DASHBOARDS"
echo "======================================================================"
python3 tests/prepopulate_scenario1_intro.py
python3 tests/prepopulate_scenario2_ops.py
python3 tests/prepopulate_scenario3_security.py
python3 tests/prepopulate_scenario4_memory.py

echo ""
echo "======================================================================"
echo "🏆 END-TO-END WORKSHOP & PROMPT VERIFICATION COMPLETED SUCCESSFULLY!"
echo "======================================================================"
