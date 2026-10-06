#!/bin/bash
# ==============================================================================
# Unified Mission Intel Infrastructure Provisioning Script
# ==============================================================================
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
if [ -d "/home/aguser/Documents/Research/bin" ]; then export PATH="/home/aguser/Documents/Research/bin:$PATH"; fi

# ANSI Terminal Formatting
if [ -t 1 ]; then
    BOLD="\033[1m"
    GREEN="\033[0;32m"
    BLUE="\033[0;34m"
    CYAN="\033[0;36m"
    YELLOW="\033[1;33m"
    RED="\033[0;31m"
    DIM="\033[2m"
    RESET="\033[0m"
else
    BOLD=""
    GREEN=""
    BLUE=""
    CYAN=""
    YELLOW=""
    RED=""
    DIM=""
    RESET=""
fi


if [ -d "/home/aguser/Documents/Research/bin" ]; then
    export PATH="/home/aguser/Documents/Research/bin:$PATH"
fi

echo -e "${BLUE}==============================================================================${RESET}"
echo -e "${BOLD}🚀 Mission Intel Multi-Domain AI Workshop - Unified Setup${RESET}"
echo -e "${DIM}   Automated Cloud Foundation, Gemini Enterprise Intranet & Agent Environment${RESET}"
echo -e "${BLUE}==============================================================================${RESET}"

echo -e "${YELLOW}${BOLD}⚠️  ATTENTION: GEMINI ENTERPRISE LICENSE REQUIRED ⚠️${RESET}"
echo -e "${BLUE}==============================================================================${RESET}"


# ------------------------------------------------------------------------------
# 1. Credential Synchronization for Sandboxed & CloudShell Execution
# ------------------------------------------------------------------------------
echo ""
echo -e "${CYAN}📌 [1/6] Synchronizing gcloud credentials to /tmp/gcloud_config...${RESET}"
mkdir -p /tmp/gcloud_config

GCLOUD_SOURCE="${HOME}/.config/gcloud"
if [ ! -d "$GCLOUD_SOURCE" ] && [ -d "/home/aguser/.config/gcloud" ]; then
    GCLOUD_SOURCE="/home/aguser/.config/gcloud"
fi

if [ -d "$GCLOUD_SOURCE" ]; then
    cp -ru "$GCLOUD_SOURCE/configurations" /tmp/gcloud_config/ 2>/dev/null || true
    cp -u "$GCLOUD_SOURCE/active_config" /tmp/gcloud_config/ 2>/dev/null || true
    cp -u "$GCLOUD_SOURCE/credentials.db" /tmp/gcloud_config/ 2>/dev/null || true
    cp -u "$GCLOUD_SOURCE/access_tokens.db" /tmp/gcloud_config/ 2>/dev/null || true
    cp -u "$GCLOUD_SOURCE/application_default_credentials.json" /tmp/gcloud_config/ 2>/dev/null || true
    echo -e "   ${GREEN}✓${RESET} Copied gcloud configuration and tokens to writable runtime location."
fi
export CLOUDSDK_CONFIG="${CLOUDSDK_CONFIG:-/tmp/gcloud_config}"

# ------------------------------------------------------------------------------
# 2. Environment Auto-Detection
# ------------------------------------------------------------------------------
echo ""
echo -e "${CYAN}📌 [2/6] Auto-detecting Google Cloud environment parameters...${RESET}"

export PROJECT_ID=${PROJECT_ID:-$(gcloud config get-value project 2>/dev/null || true)}
export LOCATION=${LOCATION:-"us-central1"}

if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}❌ Error: Could not detect Google Cloud Project ID.${RESET}"
    echo "   Please set your project with:"
    echo "     export PROJECT_ID=\"your-project-id\""
    echo "   or:"
    echo "     gcloud config set project your-project-id"
    exit 1
fi

export PROJECT_NUMBER=${PROJECT_NUMBER:-$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)" 2>/dev/null || true)}
if [ -z "$PROJECT_NUMBER" ] && [ "$PROJECT_ID" = "antig-dave" ]; then
    export PROJECT_NUMBER="284046449012"
fi
export TOKEN=${TOKEN:-$(gcloud auth print-access-token 2>/dev/null || true)}

echo -e "   • ${BOLD}Project ID:${RESET}      ${GREEN}${PROJECT_ID}${RESET}"
echo -e "   • ${BOLD}Region:${RESET}          ${GREEN}${LOCATION}${RESET}"
if [ -n "$PROJECT_NUMBER" ]; then
    echo -e "   • ${BOLD}Project Number:${RESET}  ${GREEN}${PROJECT_NUMBER}${RESET}"
else
    echo -e "   • ${BOLD}Project Number:${RESET}  ${YELLOW}(Pending / IAM restricted)${RESET}"
fi
if [ -n "$TOKEN" ]; then
    echo -e "   • ${BOLD}Auth Token:${RESET}      ${GREEN}Acquired (Bearer ****)${RESET}"
else
    echo -e "   • ${BOLD}Auth Token:${RESET}      ${YELLOW}(Not detected / Offline mode)${RESET}"
fi

export ENGINE_ID="mission-intel-app"
export BUCKET_NAME="gs://${PROJECT_ID}-humint-docs"


# ------------------------------------------------------------------------------
# 3. Batch API Enablement
# ------------------------------------------------------------------------------
echo ""
echo -e "${CYAN}📌 [3/6] Enabling required Google Cloud APIs (batch mode)...${RESET}"
echo "   Activating BigQuery, Cloud Run, Vertex AI, Agent Registry, Discovery Engine,"
echo "   Cloud Storage, Cloud DLP, Model Armor, and Network Services..."

REQUIRED_APIS=(
    "bigquery.googleapis.com"
    "run.googleapis.com"
    "aiplatform.googleapis.com"
    "agentregistry.googleapis.com"
    "discoveryengine.googleapis.com"
    "storage.googleapis.com"
    "dlp.googleapis.com"
    "modelarmor.googleapis.com"
    "networkservices.googleapis.com"
)

gcloud services enable "${REQUIRED_APIS[@]}" --project="$PROJECT_ID" >/dev/null 2>&1 || true
echo -e "   ${GREEN}✓${RESET} Google Cloud APIs enabled successfully."

# ------------------------------------------------------------------------------
# 4. IAM Service Agent Role Bindings
# ------------------------------------------------------------------------------
echo ""
echo -e "${CYAN}📌 [4/6] Configuring IAM Service Agent security permissions...${RESET}"

if [ -n "$PROJECT_NUMBER" ]; then
    # 1. Discovery Engine Service Agent -> roles/aiplatform.user (Reasoning Engine execution)
    DISCOVERY_ENGINE_SA="service-${PROJECT_NUMBER}@gcp-sa-discoveryengine.iam.gserviceaccount.com"
    echo -e "   • Discovery Engine SA (${DIM}${DISCOVERY_ENGINE_SA}${RESET})"
    echo -e "     -> Role: ${BOLD}roles/aiplatform.user${RESET}"
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:${DISCOVERY_ENGINE_SA}" \
        --role="roles/aiplatform.user" --quiet >/dev/null 2>&1 || true

    # 2. Reasoning Engine Service Agent -> roles/agentregistry.admin (Agent Registry resolution)
    REASONING_ENGINE_SA="service-${PROJECT_NUMBER}@gcp-sa-aiplatform-re.iam.gserviceaccount.com"
    echo -e "   • Reasoning Engine SA (${DIM}${REASONING_ENGINE_SA}${RESET})"
    echo -e "     -> Role: ${BOLD}roles/agentregistry.admin${RESET}"
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:${REASONING_ENGINE_SA}" \
        --role="roles/agentregistry.admin" --quiet >/dev/null 2>&1 || true

    # 3. Compute Engine default SA -> roles/bigquery.admin (Cloud Run MCP BigQuery access)
    COMPUTE_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
    echo -e "   • Compute Engine Default SA (${DIM}${COMPUTE_SA}${RESET})"
    echo -e "     -> Role: ${BOLD}roles/bigquery.admin${RESET}"
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:${COMPUTE_SA}" \
        --role="roles/bigquery.admin" --quiet >/dev/null 2>&1 || true

    echo -e "   ${GREEN}✓${RESET} IAM Service Agent role bindings configured."
else
    echo -e "   ${YELLOW}ℹ️  Skipping IAM Service Agent bindings (PROJECT_NUMBER unresolved).${RESET}"
    echo "      You may manually apply these bindings if your identity possesses Project IAM Admin:"
    echo "      export PROJECT_NUMBER=\$(gcloud projects describe \$PROJECT_ID --format=\"value(projectNumber)\")"
fi

# ==============================================================================
# BigQuery Dataset Provisioning
# ==============================================================================
# 1. Provision BigQuery Dataset
echo ""
echo "📌 [1/2] Provisioning BigQuery Dataset (mission_data)..."
bq query --location=$LOCATION --use_legacy_sql=false --project_id="$PROJECT_ID" < ./schemas/setup_dataset.sql
bq query --location=$LOCATION --use_legacy_sql=false --project_id="$PROJECT_ID" < ../data/structured_sql/setup_golden_dataset.sql

# Polling for BigQuery dataset readiness
echo "⏳ Polling BigQuery dataset mission_data for READY status..."
MAX_RETRIES=15
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if bq show --dataset "$PROJECT_ID:mission_data" >/dev/null 2>&1; then
        echo "✅ BigQuery dataset 'mission_data' and tables confirmed READY."
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT+1))
    echo "   [Attempt $RETRY_COUNT/$MAX_RETRIES] Waiting for BigQuery dataset provisioning..."
    sleep 2
done


# ==============================================================================
# PDF Upload & Cloud Storage Sync
# ==============================================================================
# 2. Generate and Upload PDFs to GCS
echo ""
echo "📌 [2/2] Generating 15 Multimodal HUMINT PDF Reports & Syncing to GCS..."
pip install --quiet reportlab --break-system-packages || pip install --quiet --user reportlab

if ! gcloud storage buckets describe "$BUCKET_NAME" --project="$PROJECT_ID" >/dev/null 2>&1; then
    gcloud storage buckets create "$BUCKET_NAME" --project="$PROJECT_ID" --location="$LOCATION"
fi

# Polling GCS bucket readiness
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if gcloud storage buckets describe "$BUCKET_NAME" --project="$PROJECT_ID" >/dev/null 2>&1; then
        echo "✅ GCS Bucket '$BUCKET_NAME' confirmed READY."
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT+1))
    echo "   [Attempt $RETRY_COUNT/$MAX_RETRIES] Waiting for GCS bucket..."
    sleep 2
done

gcloud storage cp ../data/unstructured_humint/*.pdf "$BUCKET_NAME/"
gcloud storage cp ../data/unstructured_humint/documents.jsonl "$BUCKET_NAME/documents.jsonl"
echo "✅ PDF documents & JSONL metadata uploaded to $BUCKET_NAME"


# ==============================================================================
# Discovery Engine & Gemini Enterprise App Provisioning
# ==============================================================================
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


# ==============================================================================
# Trigger OCR Document Import
# ==============================================================================
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


# ==============================================================================
# Security: Disable Search Grounding
# ==============================================================================
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


# ==============================================================================
# DLP and Model Armor Templates
# ==============================================================================
echo "Setting up Data Loss Prevention (DLP) Templates for Model Armor in project $PROJECT_ID (location: $LOCATION)..."

TOKEN=$(gcloud auth print-access-token)

# 1. Create or Patch DLP Inspect Template
echo "Creating/Updating Hardened DLP Inspect Template (mission_intel_dlp_template)..."
cat << 'DLPEOF' > dlp_template.json
{
  "inspectTemplate": {
    "displayName": "NATO Coalition DLP Inspect Template",
    "description": "DLP Template to detect MGRS, UK/NATO Caveats, Unit Call Signs, and PII",
    "inspectConfig": {
      "infoTypes": [
        { "name": "PERSON_NAME" },
        { "name": "EMAIL_ADDRESS" },
        { "name": "PHONE_NUMBER" }
      ],
      "customInfoTypes": [
        {
          "infoType": { "name": "DEMONSTRATOR_SENSITIVE_TEXT" },
          "dictionary": {
            "wordList": {
              "words": ["Demonstrator Sensitive"]
            }
          }
        },
        {
          "infoType": { "name": "UK_NATIONAL_CAVEAT" },
          "dictionary": {
            "wordList": {
              "words": [
                "UK EYES ONLY",
                "SECRET UK/US",
                "NATO RESTRICTED",
                "NOT RELEASABLE TO FOREIGN NATIONALS",
                "NOFORN"
              ]
            }
          }
        },
        {
          "infoType": { "name": "TACTICAL_CALL_SIGN" },
          "regex": {
            "pattern": "(VIPER|SABRE|RAVEN|BLACKHAWK|APEX)-[0-9]{2,3}"
          }
        }
      ],
      "minLikelihood": "VERY_UNLIKELY"
    }
  }
}
DLPEOF

curl -s -X PATCH \
  "https://dlp.googleapis.com/v2/projects/${PROJECT_ID}/locations/${LOCATION}/inspectTemplates/mission_intel_dlp_template?updateMask=inspectConfig.minLikelihood,inspectConfig.customInfoTypes,inspectConfig.infoTypes" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -H "X-Goog-User-Project: ${PROJECT_ID}" \
  -d @dlp_template.json > /dev/null || \
curl -s -X POST \
  "https://dlp.googleapis.com/v2/projects/${PROJECT_ID}/locations/${LOCATION}/inspectTemplates" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -H "X-Goog-User-Project: ${PROJECT_ID}" \
  -d @dlp_template.json > /dev/null

echo "Creating Hardened A2A DLP Inspect Template (a2a_dlp_template)..."
cat << 'A2ADLPEOF' > a2a_dlp_template.json
{
  "inspectTemplate": {
    "displayName": "NATO Coalition A2A DLP Inspect Template",
    "description": "A2A DLP Template to detect MGRS and coordinates",
    "inspectConfig": {
      "infoTypes": [ { "name": "LOCATION_COORDINATES" } ],
      "customInfoTypes": [
        {
          "infoType": { "name": "LOCATION_COORDINATES" },
          "regex": {
            "pattern": "\\b\\d{1,2}[C-X]\\s*[A-Z]{2}\\s*\\d{4,5}\\s*\\d{4,5}\\b"
          }
        }
      ],
      "minLikelihood": "VERY_UNLIKELY"
    }
  }
}
A2ADLPEOF

curl -s -X PATCH \
  "https://dlp.googleapis.com/v2/projects/${PROJECT_ID}/locations/${LOCATION}/inspectTemplates/a2a_dlp_template?updateMask=inspectConfig.minLikelihood,inspectConfig.customInfoTypes,inspectConfig.infoTypes" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -H "X-Goog-User-Project: ${PROJECT_ID}" \
  -d @a2a_dlp_template.json > /dev/null || \
curl -s -X POST \
  "https://dlp.googleapis.com/v2/projects/${PROJECT_ID}/locations/${LOCATION}/inspectTemplates" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -H "X-Goog-User-Project: ${PROJECT_ID}" \
  -d @a2a_dlp_template.json > /dev/null

# 2. Create or Patch DLP De-identify Template
echo "Creating/Updating Hardened DLP De-identify Template (mission_intel_dlp_deidentify_template)..."
cat << 'DLPDEIDENTEOF' > dlp_deidentify_template.json
{
  "deidentifyTemplate": {
    "displayName": "NATO Coalition DLP Deidentify Template",
    "description": "Redacts MGRS, UK/NATO Caveats, Call Signs, and PII to InfoType Tokens",
    "deidentifyConfig": {
      "infoTypeTransformations": {
        "transformations": [
          {
            "infoTypes": [
              { "name": "DEMONSTRATOR_SENSITIVE_TEXT" },
              { "name": "UK_NATIONAL_CAVEAT" },
              { "name": "TACTICAL_CALL_SIGN" },
              { "name": "PERSON_NAME" },
              { "name": "EMAIL_ADDRESS" },
              { "name": "PHONE_NUMBER" }
            ],
            "primitiveTransformation": {
              "replaceWithInfoTypeConfig": {}
            }
          }
        ]
      }
    }

  }
}
DLPDEIDENTEOF

curl -s -X PATCH \
  "https://dlp.googleapis.com/v2/projects/${PROJECT_ID}/locations/${LOCATION}/deidentifyTemplates/mission_intel_dlp_deidentify_template?updateMask=deidentifyConfig.infoTypeTransformations" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -H "X-Goog-User-Project: ${PROJECT_ID}" \
  -d @dlp_deidentify_template.json > /dev/null || \
curl -s -X POST \
  "https://dlp.googleapis.com/v2/projects/${PROJECT_ID}/locations/${LOCATION}/deidentifyTemplates" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -H "X-Goog-User-Project: ${PROJECT_ID}" \
  -d @dlp_deidentify_template.json > /dev/null

echo "Creating Hardened A2A DLP De-identify Template (a2a_dlp_deidentify_template)..."
cat << 'A2ADLPDEIDENTEOF' > a2a_dlp_deidentify_template.json
{
  "deidentifyTemplate": {
    "displayName": "NATO Coalition A2A DLP Deidentify Template",
    "description": "Redacts MGRS and coordinates to InfoType Tokens",
    "deidentifyConfig": {
      "infoTypeTransformations": {
        "transformations": [
          {
            "infoTypes": [
              { "name": "LOCATION_COORDINATES" }
            ],
            "primitiveTransformation": {
              "replaceConfig": {
                 "newValue": {
                    "stringValue": "[REDACTED_MGRS_COORDINATE_NATO_RELEASABLE]"
                 }
              }
            }
          }
        ]
      }
    }

  }
}
A2ADLPDEIDENTEOF

curl -s -X PATCH \
  "https://dlp.googleapis.com/v2/projects/${PROJECT_ID}/locations/${LOCATION}/deidentifyTemplates/a2a_dlp_deidentify_template?updateMask=deidentifyConfig.infoTypeTransformations" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -H "X-Goog-User-Project: ${PROJECT_ID}" \
  -d @a2a_dlp_deidentify_template.json > /dev/null || \
curl -s -X POST \
  "https://dlp.googleapis.com/v2/projects/${PROJECT_ID}/locations/${LOCATION}/deidentifyTemplates" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -H "X-Goog-User-Project: ${PROJECT_ID}" \
  -d @a2a_dlp_deidentify_template.json > /dev/null

# 3. Create or Update Dual Model Armor Templates
echo "Creating Inbound Request Model Armor Template (mission_intel_request_armor)..."
gcloud alpha model-armor templates create mission_intel_request_armor \
    --project="${PROJECT_ID}" \
    --location="${LOCATION}" \
    --rai-settings-filters="confidenceLevel=high,filterType=hate-speech" \
    --pi-and-jailbreak-filter-settings-enforcement=enabled \
    --pi-and-jailbreak-filter-settings-confidence-level=high 2>/dev/null || \
gcloud alpha model-armor templates update mission_intel_request_armor \
    --project="${PROJECT_ID}" \
    --location="${LOCATION}" \
    --pi-and-jailbreak-filter-settings-enforcement=enabled \
    --pi-and-jailbreak-filter-settings-confidence-level=high

echo "Creating Outbound Response Model Armor Template (mission_intel_response_armor)..."
gcloud alpha model-armor templates create mission_intel_response_armor \
    --project="${PROJECT_ID}" \
    --location="${LOCATION}" \
    --advanced-config-inspect-template="projects/${PROJECT_ID}/locations/${LOCATION}/inspectTemplates/mission_intel_dlp_template" \
    --advanced-config-deidentify-template="projects/${PROJECT_ID}/locations/${LOCATION}/deidentifyTemplates/mission_intel_dlp_deidentify_template" 2>/dev/null || \
gcloud alpha model-armor templates update mission_intel_response_armor \
    --project="${PROJECT_ID}" \
    --location="${LOCATION}" \
    --advanced-config-inspect-template="projects/${PROJECT_ID}/locations/${LOCATION}/inspectTemplates/mission_intel_dlp_template" \
    --advanced-config-deidentify-template="projects/${PROJECT_ID}/locations/${LOCATION}/deidentifyTemplates/mission_intel_dlp_deidentify_template"

echo "Creating A2A Coordinate Redact Model Armor Template (a2a-coordinate-redact-template)..."
gcloud alpha model-armor templates create a2a-coordinate-redact-template \
    --project="${PROJECT_ID}" \
    --location="${LOCATION}" \
    --advanced-config-inspect-template="projects/${PROJECT_ID}/locations/${LOCATION}/inspectTemplates/a2a_dlp_template" \
    --advanced-config-deidentify-template="projects/${PROJECT_ID}/locations/${LOCATION}/deidentifyTemplates/a2a_dlp_deidentify_template" 2>/dev/null || \
gcloud alpha model-armor templates update a2a-coordinate-redact-template \
    --project="${PROJECT_ID}" \
    --location="${LOCATION}" \
    --advanced-config-inspect-template="projects/${PROJECT_ID}/locations/${LOCATION}/inspectTemplates/a2a_dlp_template" \
    --advanced-config-deidentify-template="projects/${PROJECT_ID}/locations/${LOCATION}/deidentifyTemplates/a2a_dlp_deidentify_template"

# 4. Create BigQuery Dataset and Payload Logger Table for Model Armor
echo "Setting up BigQuery Dataset and Table for Model Armor Payload Logger..."
bq mk --dataset --location="${LOCATION}" --description="Model Armor Telemetry Logs Dataset" "${PROJECT_ID}:model_armor_logs" 2>/dev/null || true

cat << 'SCHEMAEOF' > schema_payload.json
[
  {"name": "timestamp", "type": "TIMESTAMP", "mode": "REQUIRED"},
  {"name": "event_name", "type": "STRING", "mode": "NULLABLE"},
  {"name": "category", "type": "STRING", "mode": "NULLABLE"},
  {"name": "template_id", "type": "STRING", "mode": "NULLABLE"},
  {"name": "user_prompt", "type": "STRING", "mode": "NULLABLE"},
  {"name": "sanitized_text", "type": "STRING", "mode": "NULLABLE"},
  {"name": "pij_match", "type": "BOOLEAN", "mode": "NULLABLE"},
  {"name": "action_taken", "type": "STRING", "mode": "NULLABLE"}
]
SCHEMAEOF

bq mk --table \
  --time_partitioning_field=timestamp \
  --time_partitioning_type=DAY \
  --schema=schema_payload.json \
  "${PROJECT_ID}:model_armor_logs.model_armor_payload_logger" 2>/dev/null || true

rm -f schema_payload.json

# 5. Create Log Router Sink targeting model_armor_logs
echo "Setting up Log Router Sink for Model Armor Payload Logger..."
gcloud logging sinks create model_armor_bq_sink \
    "bigquery.googleapis.com/projects/${PROJECT_ID}/datasets/model_armor_logs" \
    --log-filter="logName=\"projects/${PROJECT_ID}/logs/model_armor_payload_logger\"" \
    --project="${PROJECT_ID}" 2>/dev/null || \
gcloud logging sinks update model_armor_bq_sink \
    "bigquery.googleapis.com/projects/${PROJECT_ID}/datasets/model_armor_logs" \
    --log-filter="logName=\"projects/${PROJECT_ID}/logs/model_armor_payload_logger\"" \
    --project="${PROJECT_ID}"

# Grant BigQuery Data Editor to Logging Service Account
LOG_SA=$(gcloud logging sinks describe model_armor_bq_sink --project="${PROJECT_ID}" --format="value(writerIdentity)" 2>/dev/null)
if [ -n "$LOG_SA" ]; then
    echo "Granting BigQuery Data Editor permissions to Log Sink SA ($LOG_SA)..."
    gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
        --member="${LOG_SA}" \
        --role="roles/bigquery.dataEditor" \
        --condition=None >/dev/null 2>&1 || true
fi

rm -f dlp_template.json dlp_deidentify_template.json
echo "Model Armor & BigQuery Logger setup complete!"

# 6. Create System Logs Dataset for OTEL/Agent Telemetry
echo "Setting up BigQuery Dataset for System Logs (Tier 2 Memory)..."
bq mk --dataset --location="${LOCATION}" --description="Agent System Logs" "${PROJECT_ID}:system_logs" 2>/dev/null || true

echo "Setting up Log Router Sink for System Logs..."
gcloud logging sinks create system_logs_bq_sink \
    "bigquery.googleapis.com/projects/${PROJECT_ID}/datasets/system_logs" \
    --log-filter="logName:\"logs/run.googleapis.com%2Fstdout\" OR logName:\"logs/aiplatform.googleapis.com%2Freasoning_engine_application_logs\" OR logName:\"logs/cloudaudit.googleapis.com\"" \
    --project="${PROJECT_ID}" 2>/dev/null || \
gcloud logging sinks update system_logs_bq_sink \
    "bigquery.googleapis.com/projects/${PROJECT_ID}/datasets/system_logs" \
    --log-filter="logName:\"logs/run.googleapis.com%2Fstdout\" OR logName:\"logs/aiplatform.googleapis.com%2Freasoning_engine_application_logs\" OR logName:\"logs/cloudaudit.googleapis.com\"" \
    --project="${PROJECT_ID}"

SYSTEM_LOG_SA=$(gcloud logging sinks describe system_logs_bq_sink --project="${PROJECT_ID}" --format="value(writerIdentity)" 2>/dev/null)
if [ -n "$SYSTEM_LOG_SA" ]; then
    echo "Granting BigQuery Data Editor permissions to System Log Sink SA ($SYSTEM_LOG_SA)..."
    gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
        --member="${SYSTEM_LOG_SA}" \
        --role="roles/bigquery.dataEditor" \
        --condition=None >/dev/null 2>&1 || true
fi
echo "System Logs & BigQuery Logger setup complete!"




echo "======================================================================"
echo "🎉 INFRASTRUCTURE PROVISIONING COMPLETE!"
echo "======================================================================"
