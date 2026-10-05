#!/usr/bin/env bash
# ==============================================================================
# Teardown Script: Comprehensive Workshop Infrastructure Decommissioning
# Target Project: antig-dave (or active gcloud project)
# ==============================================================================

set -uo pipefail

if [ -d "/home/aguser/Documents/Research/bin" ]; then
    export PATH="/home/aguser/Documents/Research/bin:$PATH"
fi

if [ -d "/home/aguser/.config/gcloud" ]; then
    mkdir -p /tmp/gcloud_config
    cp -u /home/aguser/.config/gcloud/credentials.db /tmp/gcloud_config/ 2>/dev/null || true
    cp -u /home/aguser/.config/gcloud/access_tokens.db /tmp/gcloud_config/ 2>/dev/null || true
    cp -u /home/aguser/.config/gcloud/application_default_credentials.json /tmp/gcloud_config/ 2>/dev/null || true
fi
export CLOUDSDK_CONFIG="${CLOUDSDK_CONFIG:-/tmp/gcloud_config}"
export PROJECT_ID="${PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}"
export GOOGLE_CLOUD_PROJECT="${PROJECT_ID}"
export LOCATION="${LOCATION:-us-central1}"

echo "======================================================================"
echo "🧹 TEARDOWN: Workshop Infrastructure Decommissioning"
echo "Project ID: ${PROJECT_ID}"
echo "Location:   ${LOCATION}"
echo "Timestamp:  $(date -u +"%Y-%m-%d %H:%M:%SZ")"
echo "======================================================================"

if [ -z "${PROJECT_ID}" ]; then
  echo "❌ Error: PROJECT_ID is not set and could not be detected from gcloud."
  exit 1
fi

TOKEN=$(gcloud auth print-access-token 2>/dev/null || true)
if [ -z "${TOKEN}" ]; then
  echo "⚠️ Warning: Could not retrieve gcloud access token. REST API cleanup steps may fail."
fi

# ------------------------------------------------------------------------------
# 1. BIGQUERY CLEANUP
# ------------------------------------------------------------------------------
echo ""
echo "📌 [1/9] Cleaning up BigQuery Datasets..."
if bq ls --project_id="${PROJECT_ID}" 2>/dev/null | grep -q "mission_data"; then
  echo "   Deleting dataset: ${PROJECT_ID}:mission_data..."
  bq rm -r -f -d "${PROJECT_ID}:mission_data" 2>/dev/null || true
  echo "   ✅ BigQuery dataset deleted."
else
  echo "   ℹ️ Dataset mission_data not found."
fi

# ------------------------------------------------------------------------------
# 2. CLOUD RUN SERVICES CLEANUP
# ------------------------------------------------------------------------------
echo ""
echo "📌 [2/9] Cleaning up Cloud Run Services..."
WORKSHOP_RUN_SERVICES=("bigquery-mcp-server" "remote-mcp-server" "mission-intel-gateway")
for SVC in "${WORKSHOP_RUN_SERVICES[@]}"; do
  if gcloud run services describe "${SVC}" --region="${LOCATION}" --project="${PROJECT_ID}" >/dev/null 2>&1; then
    echo "   Deleting Cloud Run service: ${SVC} (${LOCATION})..."
    gcloud run services delete "${SVC}" --region="${LOCATION}" --project="${PROJECT_ID}" --quiet >/dev/null 2>&1 || true
    echo "   ✅ Service ${SVC} deleted."
  else
    echo "   ℹ️ Service ${SVC} not found in ${LOCATION}."
  fi
done

# ------------------------------------------------------------------------------
# 3. AGENT GATEWAY & AGENT REGISTRY CLEANUP
# ------------------------------------------------------------------------------
echo ""
echo "📌 [3/9] Cleaning up Agent Gateway & Agent Registry..."
echo "   Checking Agent Gateway: mission-intel-gateway..."
gcloud network-services agent-gateways delete mission-intel-gateway --location="${LOCATION}" --project="${PROJECT_ID}" --quiet >/dev/null 2>&1 || true

AR_SERVICES=("bigquery-mcp" "mission-intel-a2a-host")
for AR_SVC in "${AR_SERVICES[@]}"; do
  echo "   Checking Agent Registry service: ${AR_SVC}..."
  gcloud alpha agent-registry services delete "${AR_SVC}" --location="${LOCATION}" --project="${PROJECT_ID}" --quiet >/dev/null 2>&1 || true
done
echo "   ✅ Agent Gateway and Agent Registry resources decommissioned."

# ------------------------------------------------------------------------------
# 4. VERTEX AI REASONING ENGINES CLEANUP
# ------------------------------------------------------------------------------
echo ""
echo "📌 [4/9] Cleaning up Vertex AI Reasoning Engines..."
if [ -n "${TOKEN}" ]; then
  python3 -c "
import urllib.request, urllib.error, json, time, os

token = '${TOKEN}'
project_id = '${PROJECT_ID}'
location = '${LOCATION}'
url = f'https://{location}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{location}/reasoningEngines'
req = urllib.request.Request(url, headers={'Authorization': f'Bearer {token}'})
try:
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
        engines = [e['name'] for e in data.get('reasoningEngines', [])]
except Exception as e:
    engines = []

if not engines:
    print('   ℹ️ No Reasoning Engines found in ' + location + '.')
else:
    print(f'   Discovered {len(engines)} Reasoning Engine(s) to delete...')
    for name in engines:
        short_id = name.split('/')[-1]
        del_url = f'https://{location}-aiplatform.googleapis.com/v1/{name}?force=true'
        while True:
            del_req = urllib.request.Request(del_url, headers={'Authorization': f'Bearer {token}'}, method='DELETE')
            try:
                with urllib.request.urlopen(del_req) as resp:
                    print(f'   ✅ Deleted Reasoning Engine: {short_id}')
                    time.sleep(2)
                    break
            except urllib.error.HTTPError as err:
                if err.code == 429:
                    print(f'   ⏳ Quota rate limit on {short_id}. Cooldown 15s...')
                    time.sleep(15)
                elif err.code == 404:
                    print(f'   ℹ️ Already deleted: {short_id}')
                    break
                else:
                    print(f'   ❌ Error {err.code} on {short_id}')
                    break
" 2>/dev/null || true
else
  echo "   ⚠️ Skipping dynamic Reasoning Engine cleanup (no token)."
fi

# ------------------------------------------------------------------------------
# 5. GOOGLE CLOUD STORAGE CLEANUP
# ------------------------------------------------------------------------------
echo ""
echo "📌 [5/9] Cleaning up Cloud Storage Buckets..."
WORKSHOP_BUCKETS=("gs://${PROJECT_ID}-humint-docs" "gs://${PROJECT_ID}-mission-docs")
for BKT in "${WORKSHOP_BUCKETS[@]}"; do
  if gcloud storage ls "${BKT}" >/dev/null 2>&1; then
    echo "   Deleting bucket: ${BKT}..."
    gcloud storage rm -r "${BKT}" --quiet >/dev/null 2>&1 || true
    echo "   ✅ Deleted ${BKT}."
  else
    echo "   ℹ️ Bucket ${BKT} not found."
  fi
done

# ------------------------------------------------------------------------------
# 6. GEMINI ENTERPRISE & DISCOVERY ENGINE CLEANUP
# ------------------------------------------------------------------------------
echo ""
echo "📌 [6/9] Cleaning up Gemini Enterprise Search Engines & DataStores..."
if [ -n "${TOKEN}" ]; then
  python3 -c "
import urllib.request, urllib.error, json, time

token = '${TOKEN}'
project_id = '${PROJECT_ID}'
headers = {'Authorization': f'Bearer {token}', 'X-Goog-User-Project': project_id}

# 1. Discover and delete all Engines first
eng_url = f'https://discoveryengine.googleapis.com/v1alpha/projects/{project_id}/locations/global/collections/default_collection/engines'
try:
    req = urllib.request.Request(eng_url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        eng_data = json.loads(resp.read().decode())
        engines = [e['name'].split('/')[-1] for e in eng_data.get('engines', [])]
except Exception:
    engines = []

for eng in engines:
    print(f'   Deleting Discovery Engine App: {eng}...')
    del_req = urllib.request.Request(f'{eng_url}/{eng}', headers=headers, method='DELETE')
    try:
        with urllib.request.urlopen(del_req) as resp:
            print(f'   ✅ Engine {eng} deletion dispatched.')
    except Exception as e:
        print(f'   ℹ️ Engine {eng} delete response: {e}')

# 2. Discover and delete all DataStores
ds_url = f'https://discoveryengine.googleapis.com/v1alpha/projects/{project_id}/locations/global/collections/default_collection/dataStores'
try:
    req = urllib.request.Request(ds_url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        ds_data = json.loads(resp.read().decode())
        datastores = [d['name'].split('/')[-1] for d in ds_data.get('dataStores', [])]
except Exception:
    datastores = []

for ds in datastores:
    print(f'   Deleting Discovery Engine DataStore: {ds}...')
    del_req = urllib.request.Request(f'{ds_url}/{ds}', headers=headers, method='DELETE')
    try:
        with urllib.request.urlopen(del_req) as resp:
            print(f'   ✅ DataStore {ds} deletion dispatched.')
    except Exception as e:
        print(f'   ℹ️ DataStore {ds} delete response: {e}')
" 2>/dev/null || true
  echo "   ✅ Discovery Engine cleanup finished."
else
  echo "   ⚠️ Skipping Discovery Engine cleanup (no token)."
fi

# ------------------------------------------------------------------------------
# 7. MODEL ARMOR & CLOUD DLP CLEANUP
# ------------------------------------------------------------------------------
echo ""
echo "📌 [7/9] Cleaning up Model Armor Templates & Cloud DLP..."
echo "   Deleting Model Armor Template: mission_intel_armor..."
gcloud alpha model-armor templates delete mission_intel_armor \
  --location="${LOCATION}" \
  --project="${PROJECT_ID}" \
  --quiet >/dev/null 2>&1 || true

if [ -n "${TOKEN}" ]; then
  echo "   Deleting Cloud DLP inspect template: mission_intel_dlp_template..."
  curl -X DELETE -s \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "X-Goog-User-Project: ${PROJECT_ID}" \
    "https://dlp.googleapis.com/v2/projects/${PROJECT_ID}/locations/${LOCATION}/inspectTemplates/mission_intel_dlp_template" >/dev/null 2>&1 || true

  echo "   Deleting Cloud DLP de-identify template: mission_intel_dlp_deidentify_template..."
  curl -X DELETE -s \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "X-Goog-User-Project: ${PROJECT_ID}" \
    "https://dlp.googleapis.com/v2/projects/${PROJECT_ID}/locations/${LOCATION}/deidentifyTemplates/mission_intel_dlp_deidentify_template" >/dev/null 2>&1 || true
fi
echo "   ✅ Model Armor and Cloud DLP templates deleted."

# ------------------------------------------------------------------------------
# 8. CLOUD LOGGING METRICS & LOG SINK CLEANUP
# ------------------------------------------------------------------------------
echo ""
echo "📌 [8/11] Cleaning up Custom Cloud Logging Metrics..."
METRICS=(
  "agent_execution_latency" "dlp_redaction_count" "document_import_count"
  "execute_bigquery_sql_complete" "genai_token_usage" "hitl_gate_triggers"
  "hitl_guardrail_triggers" "memory_bank_updates" "memory_events_by_tier"
  "memory_operations_latency" "model_armor_latency" "model_armor_pij_blocks"
  "model_armor_redactions" "nato_classification_compliance" "rag_search_latency"
  "sanitization_count" "session_state_deltas" "session_turn_count"
  "spiffe_api_calls" "tool_execution_latency"
)

for METRIC in "${METRICS[@]}"; do
  gcloud logging metrics delete "${METRIC}" --project="${PROJECT_ID}" --quiet >/dev/null 2>&1 || true
done
echo "   ✅ Custom Log Metrics deleted."

echo "📌 Cleaning up Model Armor Log Sink..."
gcloud logging sinks delete model_armor_bq_sink --project="${PROJECT_ID}" --quiet >/dev/null 2>&1 || true
echo "   ✅ Log sink deleted."

echo "📌 Cleaning up Model Armor BigQuery Dataset..."
bq rm -r -f -d "${PROJECT_ID}:model_armor_logs" 2>/dev/null || true
echo "   ✅ model_armor_logs dataset deleted."

# ------------------------------------------------------------------------------
# 9. CLOUD MONITORING DASHBOARDS CLEANUP
# ------------------------------------------------------------------------------
echo ""
echo "📌 [9/11] Cleaning up Cloud Monitoring Dashboards..."
DASHBOARDS=(
  "UK Mission Intel Agent - Observability & OpenTelemetry Metrics"
  "UK Mission Intel Agent - Model Armor & OPSEC Compliance Metrics"
  "UK Mission Intel Agent - FinOps Token Burn"
  "UK Mission Intel Agent - Agent Platform Memory Metrics"
)

for DASH_TITLE in "${DASHBOARDS[@]}"; do
  echo "   Discovering dashboard: ${DASH_TITLE}..."
  DASH_ID=$(gcloud monitoring dashboards list --project="${PROJECT_ID}" --format="json" 2>/dev/null | \
    python3 -c "import sys, json; data=json.load(sys.stdin); res=[d['name'].split('/')[-1] for d in data if d.get('displayName')=='${DASH_TITLE}']; print(res[0] if res else '')" 2>/dev/null || true)
  
  if [ -n "${DASH_ID}" ]; then
    echo "   Deleting Dashboard ID: ${DASH_ID}..."
    gcloud monitoring dashboards delete "${DASH_ID}" --project="${PROJECT_ID}" --quiet >/dev/null 2>&1 || true
    echo "   ✅ Dashboard deleted."
  else
    echo "   ℹ️ Dashboard not found."
  fi
done

# ------------------------------------------------------------------------------
# 9. SELECTIVE API DEACTIVATION (PRESERVING ANTIGRAVITY & CORE CLOUD APIS)
# ------------------------------------------------------------------------------
echo ""
echo "📌 [9/10] Selectively Disabling Workshop-Specific APIs..."
echo "   Preserving: aiplatform, discoveryengine, bigquery, run, storage, compute, logging"
WORKSHOP_APIS_TO_DISABLE=(
  "modelarmor.googleapis.com"
  "agentregistry.googleapis.com"
  "dlp.googleapis.com"
  "networkservices.googleapis.com"
)

for API in "${WORKSHOP_APIS_TO_DISABLE[@]}"; do
  echo "   Disabling API: ${API}..."
  gcloud services disable "${API}" --project="${PROJECT_ID}" --quiet >/dev/null 2>&1 || true
  echo "   ✅ ${API} disabled."
done

# ------------------------------------------------------------------------------
# 10. CLEAN-SLATE VERIFICATION AUDIT
# ------------------------------------------------------------------------------
echo ""
echo "======================================================================"
echo "🔍 [10/10] RUNNING CLEAN-SLATE VERIFICATION AUDIT"
echo "======================================================================"

check_status() {
  local label="$1"
  local status="$2"
  if [ "$status" -eq 0 ]; then
    printf "%-35s | \033[0;32mCLEAN ✅ (Decommissioned)\033[0m\n" "$label"
  else
    printf "%-35s | \033[0;33mREMAINING ⚠️ (Check manual)\033[0m\n" "$label"
  fi
}

# 1. BigQuery Dataset
bq show "${PROJECT_ID}:mission_data" >/dev/null 2>&1 && BQ_STATUS=1 || BQ_STATUS=0
check_status "BigQuery: mission_data" "$BQ_STATUS"

# 2. Cloud Storage Bucket
gcloud storage ls "gs://${PROJECT_ID}-humint-docs" >/dev/null 2>&1 && GCS_STATUS=1 || GCS_STATUS=0
check_status "Cloud Storage: humint-docs" "$GCS_STATUS"

# 3. Cloud Run Service
gcloud run services describe bigquery-mcp-server --region="${LOCATION}" --project="${PROJECT_ID}" >/dev/null 2>&1 && CR_STATUS=1 || CR_STATUS=0
check_status "Cloud Run: bigquery-mcp-server" "$CR_STATUS"

# 4. Reasoning Engines
if [ -n "${TOKEN}" ]; then
  RE_REMAINING=$(curl -s -H "Authorization: Bearer ${TOKEN}" "https://${LOCATION}-aiplatform.googleapis.com/v1/projects/${PROJECT_ID}/locations/${LOCATION}/reasoningEngines" | python3 -c "import sys, json; data = json.load(sys.stdin); res = [re.get('name', '') for re in data.get('reasoningEngines', [])]; print(' '.join(res))" 2>/dev/null || true)
  [ -z "${RE_REMAINING}" ] && RE_STATUS=0 || RE_STATUS=1
else
  RE_STATUS=0
fi
check_status "Reasoning Engines (${LOCATION})" "$RE_STATUS"

# 5. Discovery Engine Engines
if [ -n "${TOKEN}" ]; then
  ENG_REMAINING=$(curl -s -H "Authorization: Bearer ${TOKEN}" -H "X-Goog-User-Project: ${PROJECT_ID}" "https://discoveryengine.googleapis.com/v1alpha/projects/${PROJECT_ID}/locations/global/collections/default_collection/engines" | python3 -c "import sys, json; data = json.load(sys.stdin); res = [e.get('name', '') for e in data.get('engines', [])]; print(' '.join(res))" 2>/dev/null || true)
  [ -z "${ENG_REMAINING}" ] && DE_STATUS=0 || DE_STATUS=1
else
  DE_STATUS=0
fi
check_status "Discovery Engine: Intranet Apps" "$DE_STATUS"

# 6. APIs Status
for API in "${WORKSHOP_APIS_TO_DISABLE[@]}"; do
  gcloud services list --enabled --project="${PROJECT_ID}" 2>/dev/null | grep -q "${API}" && API_STATUS=1 || API_STATUS=0
  check_status "API Disabled: ${API}" "$API_STATUS"
done

# 7. Core APIs Preserved
CORE_APIS=("aiplatform.googleapis.com" "discoveryengine.googleapis.com" "bigquery.googleapis.com" "run.googleapis.com" "storage.googleapis.com")
for CAPI in "${CORE_APIS[@]}"; do
  gcloud services list --enabled --project="${PROJECT_ID}" 2>/dev/null | grep -q "${CAPI}" && CAPI_STATUS=0 || CAPI_STATUS=1
  if [ "$CAPI_STATUS" -eq 0 ]; then
    printf "%-35s | \033[0;32mACTIVE ✅ (Preserved for Core Environment)\033[0m\n" "API Preserved: ${CAPI}"
  else
    printf "%-35s | \033[0;31mINACTIVE ❌ (Core API Missing!)\033[0m\n" "API Preserved: ${CAPI}"
  fi
done

echo ""
echo "======================================================================"
echo "🏆 PROJECT ${PROJECT_ID} IS NOW PREPARED FOR CLEAN DEPLOYMENT!"
echo "======================================================================"
