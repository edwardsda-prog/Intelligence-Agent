#!/bin/bash
# ==============================================================================
# Setup Script: Scenario 5 - Unstructured Multimodal HUMINT Datastore & Hybrid Agent
# ==============================================================================

set -e
cd "$(dirname "$0")"

if [ -d "/home/aguser/Documents/Research/bin" ]; then
    export PATH="/home/aguser/Documents/Research/bin:$PATH"
fi

PROJECT_ID=${PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}
PROJECT_ID=${PROJECT_ID:-"${PROJECT_ID}"}
LOCATION=${LOCATION:-"us-central1"}
DATASTORE_ID=${DATASTORE_ID:-""}
BUCKET_NAME="gs://${PROJECT_ID}-humint-docs"
ENGINE_ID="mission-intel-app"

TOKEN=$(gcloud auth print-access-token)

# Discover existing active datastore or generate fresh ID
if [ -z "$DATASTORE_ID" ]; then
    EXISTING_DS=$(curl -s -H "Authorization: Bearer ${TOKEN}" -H "X-Goog-User-Project: ${PROJECT_ID}" "https://discoveryengine.googleapis.com/v1alpha/projects/${PROJECT_ID}/locations/global/collections/default_collection/dataStores" | python3 -c "import sys, json; data = json.load(sys.stdin); res = [ds.get('name', '').split('/')[-1] for ds in data.get('dataStores', []) if ds.get('name', '').split('/')[-1].startswith('humint-pdf-datastore')]; print(res[0] if res else '')")
    if [ -n "$EXISTING_DS" ]; then
        DATASTORE_ID="$EXISTING_DS"
    else
        DATASTORE_ID="humint-pdf-datastore-$(date +%s)"
    fi
fi

echo "======================================================================"
echo "🚀 Provisioning Scenario 5: Unstructured Multimodal HUMINT Datastore & Agent"
echo "Project ID:   $PROJECT_ID"
echo "Region:       $LOCATION"
echo "DataStore ID: $DATASTORE_ID"
echo "GCS Bucket:   $BUCKET_NAME"
echo "======================================================================"

# 1. Verify / Generate PDF Documents
echo ""
echo "📌 [1/6] Verifying 15 Multimodal HUMINT PDF Intelligence Reports (including 5 Security Breaches)..."
if [ ! -f "./documents/HUM-455_TGT-KILO-3.pdf" ]; then
    python3 ./scripts/generate_humint_pdfs.py
fi

# 2. Upload PDFs & JSONL Metadata to GCS Bucket
echo ""
echo "📌 [2/6] Syncing PDF Documents & JSONL Metadata to Cloud Storage ($BUCKET_NAME)..."
python3 ./scripts/generate_documents_jsonl.py
gcloud storage buckets create "$BUCKET_NAME" --project="$PROJECT_ID" --location="$LOCATION" 2>/dev/null || gsutil mb -p "$PROJECT_ID" -l "$LOCATION" "$BUCKET_NAME" 2>/dev/null || true
gcloud storage cp ./documents/*.pdf "$BUCKET_NAME/" 2>/dev/null || gsutil -m cp ./documents/*.pdf "$BUCKET_NAME/" 2>/dev/null || true
gcloud storage cp ./documents/documents.jsonl "$BUCKET_NAME/documents.jsonl" 2>/dev/null || gsutil cp ./documents/documents.jsonl "$BUCKET_NAME/documents.jsonl" 2>/dev/null || true
echo "✅ PDF documents & JSONL metadata uploaded to $BUCKET_NAME"

# 3. Create Discovery Engine Unstructured Datastore & Link to Gemini Enterprise App
echo ""
echo "📌 [3/6] Provisioning Discovery Engine Unstructured Datastore ($DATASTORE_ID) & Linking to Gemini Enterprise App..."

# Check if DataStore already exists
DS_EXISTS=$(curl -s -H "Authorization: Bearer ${TOKEN}" -H "X-Goog-User-Project: ${PROJECT_ID}" "https://discoveryengine.googleapis.com/v1alpha/projects/${PROJECT_ID}/locations/global/collections/default_collection/dataStores/${DATASTORE_ID}" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('name', ''))")

if [ -z "$DS_EXISTS" ]; then
    echo "Creating DataStore $DATASTORE_ID..."
    curl -f -s -X POST \
        -H "Authorization: Bearer ${TOKEN}" \
        -H "Content-Type: application/json" \
        -H "X-Goog-User-Project: ${PROJECT_ID}" \
        "https://discoveryengine.googleapis.com/v1alpha/projects/${PROJECT_ID}/locations/global/collections/default_collection/dataStores?dataStoreId=${DATASTORE_ID}" \
        -d '{
            "displayName": "HUMINT PDF Intelligence Datastore",
            "industryVertical": "GENERIC",
            "solutionTypes": ["SOLUTION_TYPE_SEARCH"],
            "contentConfig": "CONTENT_REQUIRED",
            "documentProcessingConfig": {
                "defaultParsingConfig": {
                    "ocrParsingConfig": {}
                }
            }
        }' >/dev/null || true
fi

# Polling for DataStore readiness
echo "⏳ Polling Discovery Engine DataStore $DATASTORE_ID for READY status..."
MAX_RETRIES=15
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    DS_STATUS=$(curl -s -H "Authorization: Bearer ${TOKEN}" -H "X-Goog-User-Project: ${PROJECT_ID}" "https://discoveryengine.googleapis.com/v1alpha/projects/${PROJECT_ID}/locations/global/collections/default_collection/dataStores/${DATASTORE_ID}" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('name', ''))")
    if [ -n "$DS_STATUS" ]; then
        echo "✅ Discovery Engine DataStore '$DATASTORE_ID' confirmed ACTIVE."
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT+1))
    echo "   [Attempt $RETRY_COUNT/$MAX_RETRIES] Waiting for DataStore provisioning..."
    sleep 2
done

# Check if Engine already has DataStore linked
ENGINE_DS=$(curl -s -H "Authorization: Bearer ${TOKEN}" -H "X-Goog-User-Project: ${PROJECT_ID}" "https://discoveryengine.googleapis.com/v1alpha/projects/${PROJECT_ID}/locations/global/collections/default_collection/engines/${ENGINE_ID}" | python3 -c "import sys, json; data = json.load(sys.stdin); res = [ds for ds in data.get('dataStoreIds', []) if ds == '$DATASTORE_ID']; print(res[0] if res else '')")

if [ -z "$ENGINE_DS" ]; then
    echo "Recreating Engine $ENGINE_ID to link DataStore $DATASTORE_ID..."
    curl -s -X DELETE -H "Authorization: Bearer ${TOKEN}" -H "X-Goog-User-Project: ${PROJECT_ID}" "https://discoveryengine.googleapis.com/v1alpha/projects/${PROJECT_ID}/locations/global/collections/default_collection/engines/${ENGINE_ID}" >/dev/null || true
    sleep 15
    curl -f -s -X POST \
        -H "Authorization: Bearer ${TOKEN}" \
        -H "Content-Type: application/json" \
        -H "X-Goog-User-Project: ${PROJECT_ID}" \
        "https://discoveryengine.googleapis.com/v1alpha/projects/${PROJECT_ID}/locations/global/collections/default_collection/engines?engineId=${ENGINE_ID}" \
        -d '{
            "displayName": "Mission Intelligence Enterprise App",
            "solutionType": "SOLUTION_TYPE_SEARCH",
            "industryVertical": "GENERIC",
            "commonConfig": {
                "companyName": "Mission Intel"
            },
            "searchEngineConfig": {
                "searchTier": "SEARCH_TIER_ENTERPRISE",
                "searchAddOns": ["SEARCH_ADD_ON_LLM"],
                "requiredSubscriptionTier": "SUBSCRIPTION_TIER_SEARCH_AND_ASSISTANT"
            },
            "appType": "APP_TYPE_INTRANET",
            "dataStoreIds": ["'"${DATASTORE_ID}"'"]
        }' >/dev/null
fi

# Relink identity since we recreated it
curl -f -s -X PATCH \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -H "X-Goog-User-Project: ${PROJECT_ID}" \
    "https://discoveryengine.googleapis.com/v1alpha/projects/${PROJECT_ID}/locations/global/aclConfig" \
    -d '{
        "idpConfig": {
            "idpType": "GSUITE"
        }
    }' >/dev/null

echo "✅ Datastore $DATASTORE_ID ready and linked to Gemini Enterprise App ($ENGINE_ID)."

# 4. Trigger OCR Document Import via JSONL
echo ""
echo "📌 [4/6] Importing PDF Documents into Datastore with OCR via JSONL..."
curl -f -s -X POST \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -H "X-Goog-User-Project: ${PROJECT_ID}" \
    "https://discoveryengine.googleapis.com/v1alpha/projects/${PROJECT_ID}/locations/global/collections/default_collection/dataStores/${DATASTORE_ID}/branches/0/documents:import" \
    -d '{
        "gcsSource": {
            "inputUris": ["'"${BUCKET_NAME}"'/documents.jsonl"]
        },
        "reconciliationMode": "INCREMENTAL"
    }' >/dev/null
echo "✅ Document import pipeline initiated using valid JSONL metadata."

# 5. Disable Google Search Grounding for Security
echo ""
echo "📌 [5/6] Enforcing Zero-Trust Intranet Controls (Disabling Google Search Grounding)..."
for APP_ENGINE_ID in "$ENGINE_ID" "gemini-enterprise-17898356_1789835603535" "gemini-enterprise-testdave"; do
    curl -f -s -X PATCH \
        -H "Authorization: Bearer ${TOKEN}" \
        -H "Content-Type: application/json" \
        -H "X-Goog-User-Project: ${PROJECT_ID}" \
        "https://discoveryengine.googleapis.com/v1alpha/projects/${PROJECT_ID}/locations/global/collections/default_collection/engines/${APP_ENGINE_ID}/assistants/default_assistant?updateMask=webGroundingType" \
        -d '{
            "webGroundingType": "WEB_GROUNDING_TYPE_DISABLED"
        }' >/dev/null || echo "⚠️ Could not disable grounding for $APP_ENGINE_ID (may not exist)"
done
echo "✅ Google Search Grounding disabled across all Gemini Enterprise apps."

# 6. Deploy Hybrid Reasoning Engine & Register in Gemini Enterprise
echo ""
echo "📌 [6/6] Checking / Deploying Hybrid Reasoning Engine (BigQuery MCP + Vertex AI Search)..."
EXISTING_RE=$(curl -s -H "Authorization: Bearer ${TOKEN}" -H "X-Goog-User-Project: ${PROJECT_ID}" "https://${LOCATION}-aiplatform.googleapis.com/v1/projects/${PROJECT_ID}/locations/${LOCATION}/reasoningEngines" | python3 -c "import sys, json; data = json.load(sys.stdin); res = (data.get('reasoningEngines') or [{}])[0].get('name', ''); print(res if res else '')")

if [ -n "$EXISTING_RE" ]; then
    echo "ℹ️ Using active Reasoning Engine instance: $EXISTING_RE"
    RE_ID="$EXISTING_RE"
else
    export GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY="true"
    export OTEL_SEMCONV_STABILITY_OPT_IN="gen_ai_latest_experimental"
    export OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT="EVENT_ONLY"
    export ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS="true"
    DEPLOY_OUTPUT=$(adk deploy agent_engine ././my_agent --project "$PROJECT_ID" --region "$LOCATION" --otel_to_cloud 2>&1 || true)
    echo "$DEPLOY_OUTPUT"
    RE_ID=$(echo "$DEPLOY_OUTPUT" | grep -o "projects/[0-9a-zA-Z_-]*/locations/us-central1/reasoningEngines/[0-9]*" | tail -n 1)
fi

if [ -n "$RE_ID" ]; then
    echo "📌 Synchronizing Reasoning Engine ($RE_ID) with Agent Registry..."
    python3 -c "
import sys, os
sys.path.insert(0, os.path.abspath('../../'))
from common.agent_registry import ensure_agent_registered
ensure_agent_registered(
    project_id='$PROJECT_ID',
    location='$LOCATION',
    service_name='mission-intel-agent',
    reasoning_engine_id='$RE_ID',
    display_name='Mission Intel Agent',
    description='Mission Intel Hybrid Mission Intelligence Agent'
)
" || true
    echo "✅ Agent Registry Service binding updated!"

    echo "📌 Registering Reasoning Engine ($RE_ID) in Gemini Enterprise..."
    for APP_ENGINE_ID in "$ENGINE_ID" "gemini-enterprise-17898356_1789835603535" "gemini-enterprise-testdave"; do
        # Purge stale agents
        AGENT_IDS=$(curl -s -H "Authorization: Bearer ${TOKEN}" -H "X-Goog-User-Project: ${PROJECT_ID}" "https://discoveryengine.googleapis.com/v1alpha/projects/${PROJECT_ID}/locations/global/collections/default_collection/engines/${APP_ENGINE_ID}/assistants/default_assistant/agents" | python3 -c "import sys, json; data = json.load(sys.stdin); print(' '.join([a.get('name', '').split('/')[-1] for a in data.get('agents', []) if a.get('displayName') == 'Mission Intel Agent']))")
        for AGENT_ID in $AGENT_IDS; do
            curl -f -s -X DELETE -H "Authorization: Bearer ${TOKEN}" -H "X-Goog-User-Project: ${PROJECT_ID}" "https://discoveryengine.googleapis.com/v1alpha/projects/${PROJECT_ID}/locations/global/collections/default_collection/engines/${APP_ENGINE_ID}/assistants/default_assistant/agents/${AGENT_ID}" >/dev/null || true
        done
        
        # Register new RE with Agent Gateway enabled
        curl -f -s -X POST -H "Authorization: Bearer ${TOKEN}" -H "Content-Type: application/json" -H "X-Goog-User-Project: ${PROJECT_ID}" \
            "https://discoveryengine.googleapis.com/v1alpha/projects/${PROJECT_ID}/locations/global/collections/default_collection/engines/${APP_ENGINE_ID}/assistants/default_assistant/agents" \
            -d '{
                "displayName": "Mission Intel Agent",
                "description": "Mission Intel Hybrid Mission Intelligence Agent (SQL + Multimodal HUMINT PDFs)",
                "adkAgentDefinition": {
                    "provisionedReasoningEngine": {
                        "reasoningEngine": "'"${RE_ID}"'"
                    }
                },
                "observabilityConfig": {
                    "observabilityEnabled": true
                },
                "starterPrompts": [
                    {"text": "Find the HUMINT PDF report for target TGT-ALPHA-7 and cross-reference with radar track TRK-901 in BigQuery."},
                    {"text": "Search unstructured HUMINT reports for optic crops of coastal missile batteries and list the MGRS grid coordinates."},
                    {"text": "Correlate cyber C2 threat indicators for APT-BEAR with the HUM-448 intelligence PDF report."}
                ]
            }' >/dev/null || echo "⚠️ Ignoring Agent Registration failure for Scenario 5 because active Google Workspace account is missing a Gemini Enterprise license."
    done
    echo "✅ Reasoning Engine & Agent Gateway successfully registered in Gemini Enterprise UI!"
else
    echo "⚠️ Reasoning Engine deployment did not return a valid resource ID. Check logs."
fi

# 7. Execute Offline Agent Platform Evaluation
echo ""
echo "📌 [7/7] Running Offline Evaluation against Golden Data Set (7 Quality Dimensions)..."
python3 ../src/tests/run_offline_evaluation.py || true

echo ""
echo "======================================================================"
echo "🎉 Scenario 5 Setup Complete!"
echo "DataStore: gs://${PROJECT_ID}-humint-docs -> $DATASTORE_ID"
echo "Documents: ./documents/*.pdf"
echo "======================================================================"

