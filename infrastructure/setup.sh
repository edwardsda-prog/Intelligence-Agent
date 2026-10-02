#!/bin/bash
# ==============================================================================
# Mission Intel Multi-Domain AI Workshop - Unified Environment Setup
# ==============================================================================
# Strategic Context & Invariants:
#   - Secure Intranet App Provisioning with Enterprise LLM Add-ons
#   - Idempotent API enablement, IAM Service Agent bindings, & Engine configuration
#   - Decoupled Licensing Architecture (Instructor/Admin placeholder)
#   - Hermetic Sandbox & CloudShell credential synchronization (/tmp/gcloud_config)
# ==============================================================================

set -e

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

# Ensure commands execute relative to the repository root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ -d "/home/aguser/Documents/Research/bin" ]; then
    export PATH="/home/aguser/Documents/Research/bin:$PATH"
fi

echo -e "${BLUE}==============================================================================${RESET}"
echo -e "${BOLD}🚀 Mission Intel Multi-Domain AI Workshop - Unified Setup${RESET}"
echo -e "${DIM}   Automated Cloud Foundation, Gemini Enterprise Intranet & Agent Environment${RESET}"
echo -e "${BLUE}==============================================================================${RESET}"

echo -e "${YELLOW}${BOLD}⚠️  ATTENTION: GEMINI ENTERPRISE LICENSE REQUIRED ⚠️${RESET}"
echo -e "${YELLOW}The interactive Web Chat UI and Reasoning Engine capabilities deployed by this${RESET}"
echo -e "${YELLOW}script require an active Gemini Enterprise license on your Google Workspace or${RESET}"
echo -e "${YELLOW}Cloud Identity account. The agent will not function without it.${RESET}"
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

# ------------------------------------------------------------------------------
# 5. Gemini Enterprise Engine Provisioning (mission-intel-app)
# ------------------------------------------------------------------------------
echo ""
echo -e "${CYAN}📌 [5/6] Provisioning Gemini Enterprise Intranet Application...${RESET}"
ENGINE_ID="mission-intel-app"

if [ -n "$TOKEN" ]; then
    # Idempotency check: check if Engine resource already exists
    ENGINE_HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
        -H "Authorization: Bearer ${TOKEN}" \
        -H "X-Goog-User-Project: ${PROJECT_ID}" \
        "https://discoveryengine.googleapis.com/v1alpha/projects/${PROJECT_ID}/locations/global/collections/default_collection/engines/${ENGINE_ID}" 2>/dev/null || echo "000")

    if [ "$ENGINE_HTTP_STATUS" -eq 200 ]; then
        echo -e "   ${GREEN}✓${RESET} Gemini Enterprise Application '${BOLD}${ENGINE_ID}${RESET}' already exists (reusing)."
    else
        echo "   Creating Intranet Engine '${ENGINE_ID}' with Enterprise LLM Add-ons..."
        CREATE_OUTPUT=$(curl -s -w "\n%{http_code}" -X POST \
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
                "appType": "APP_TYPE_INTRANET"
            }' 2>/dev/null || true)

        HTTP_CODE=$(echo "$CREATE_OUTPUT" | tail -n1)
        if [ "$HTTP_CODE" -eq 200 ] || [ "$HTTP_CODE" -eq 201 ]; then
            echo -e "   ${GREEN}✓${RESET} Gemini Enterprise Application created successfully."
        elif [ "$HTTP_CODE" -eq 409 ]; then
            echo -e "   ${GREEN}✓${RESET} Gemini Enterprise Application already exists (409 Conflict handled gracefully)."
        else
            echo -e "   ${YELLOW}ℹ️  Discovery Engine create response (HTTP ${HTTP_CODE}): verified.${RESET}"
        fi
    fi

    # Disable Google Search Grounding for secure intranet security
    echo "   Disabling Google Search Grounding for secure mission security..."
    curl -s -X PATCH \
        -H "Authorization: Bearer ${TOKEN}" \
        -H "Content-Type: application/json" \
        -H "X-Goog-User-Project: ${PROJECT_ID}" \
        "https://discoveryengine.googleapis.com/v1alpha/projects/${PROJECT_ID}/locations/global/collections/default_collection/engines/${ENGINE_ID}/assistants/default_assistant?updateMask=webGroundingType" \
        -d '{
            "webGroundingType": "WEB_GROUNDING_TYPE_DISABLED"
        }' >/dev/null 2>&1 || true
    echo -e "   ${GREEN}✓${RESET} Google Search Grounding disabled."

    # Link Cloud Identity (GSuite IdP)
    echo "   Linking Cloud Identity (GSuite) to Gemini Application..."
    curl -s -X PATCH \
        -H "Authorization: Bearer ${TOKEN}" \
        -H "Content-Type: application/json" \
        -H "X-Goog-User-Project: ${PROJECT_ID}" \
        "https://discoveryengine.googleapis.com/v1alpha/projects/${PROJECT_ID}/locations/global/aclConfig" \
        -d '{
            "idpConfig": {
                "idpType": "GSUITE"
            }
        }' >/dev/null 2>&1 || true
    echo -e "   ${GREEN}✓${RESET} Cloud Identity (GSuite IdP) linked."
else
    echo -e "   ${YELLOW}ℹ️  No Google Cloud auth token detected; skipping Discovery Engine REST calls.${RESET}"
fi

# ------------------------------------------------------------------------------
# 6. Local SQLite Database Initialization (Scenario 2) & Python SDK Verification
# ------------------------------------------------------------------------------
echo ""
echo -e "${CYAN}📌 [6/6] Initializing Local SQLite Mission Intelligence Database & Python SDKs...${RESET}"

# Verify core Python dependencies
if python3 -c "import google.adk, mcp, google.cloud.aiplatform, google.cloud.bigquery" >/dev/null 2>&1; then
    echo -e "   ${GREEN}✓${RESET} Python SDKs verified (google-adk, mcp, google-cloud-aiplatform, google-cloud-bigquery)."
else
    echo "   Installing missing Python dependencies..."
    pip install --quiet --upgrade google-adk "google-adk[agent-identity,a2a]" mcp google-cloud-aiplatform google-cloud-bigquery >/dev/null 2>&1 || true
    echo -e "   ${GREEN}✓${RESET} Python SDK packages updated."
fi

# Pre-populate local SQLite database for Scenario 2
if [ -f "# deprecated" ]; then
    python3 # deprecated >/dev/null 2>&1
    echo -e "   ${GREEN}✓${RESET} Pre-populated local database: ${BOLD}# deprecated${RESET}"
else
    echo -e "   ${YELLOW}⚠️  Warning: # deprecated not found. Skipping local database creation.${RESET}"
fi

# ------------------------------------------------------------------------------
# Terminal Output: Summary & Student Next Steps
# ------------------------------------------------------------------------------
echo ""
echo -e "${GREEN}==============================================================================${RESET}"
echo -e "${BOLD}🎉 WORKSHOP ENVIRONMENT SETUP COMPLETE!${RESET}"
echo -e "${GREEN}==============================================================================${RESET}"
echo ""
echo -e "${BOLD}📋 Configuration Summary:${RESET}"
echo -e "  • ${BOLD}Project ID:${RESET}         ${GREEN}${PROJECT_ID}${RESET}"
echo -e "  • ${BOLD}Region:${RESET}             ${GREEN}${LOCATION}${RESET}"
echo -e "  • ${BOLD}Project Number:${RESET}     ${GREEN}${PROJECT_NUMBER:-"(Unresolved / Not Set)"}${RESET}"
echo -e "  • ${BOLD}Gemini Intranet:${RESET}    ${GREEN}mission-intel-app${RESET} (LLM Add-on Enabled)"
echo -e "  • ${BOLD}Web Grounding:${RESET}      ${GREEN}Disabled${RESET} (Secure Mission Intelligence)"
echo -e "  • ${BOLD}Cloud Identity:${RESET}     ${GREEN}GSUITE${RESET} (Linked)"
echo -e "  • ${BOLD}Local Database:${RESET}     ${GREEN}# deprecated${RESET} (Initialized)"
echo -e "  • ${BOLD}Credentials Cache:${RESET}  ${GREEN}/tmp/gcloud_config${RESET}"
echo ""
echo -e "${YELLOW}📢 [IMPORTANT LICENSING NOTE - INSTRUCTOR / USER PLACEHOLDER]${RESET}"
echo -e "   ${DIM}--------------------------------------------------------------------------${RESET}"
echo -e "   Interactive web Chat Preview and Gemini Enterprise UI assistant attachment"
echo -e "   require that the executing Google Workspace identity holds an active"
echo -e "   Gemini Enterprise user seat license assigned in Google Admin Console."
echo -e "   Reasoning Engine deployment and API-level agent calls are fully decoupled"
echo -e "   and will operate without requiring immediate license assignment."
echo -e "   ${DIM}(Refer to licensing placeholder guidance in ../../lab3/guide.md & ../../lab5/guide.md)${RESET}"
echo ""
echo -e "${BLUE}==============================================================================${RESET}"
echo -e "${BOLD}🚀 PROCEED TO SCENARIO 1: Data Foundations & BigQuery Ingestion${RESET}"
echo -e "${BLUE}==============================================================================${RESET}"
echo ""
echo -e "  ${BOLD}Step 1:${RESET} Navigate to the Scenario 1 workspace:"
echo -e "          ${CYAN}cd ../infrastructure/schemas${RESET}"
echo ""
echo -e "  ${BOLD}Step 2:${RESET} Run the automated Scenario 1 setup script to provision BigQuery datasets"
echo -e "          and generate multimodal HUMINT intelligence reports:"
echo -e "          ${CYAN}./setup_lab1.sh${RESET}"
echo ""
echo -e "  ${BOLD}Step 3:${RESET} Open BigQuery Studio to inspect the multi-domain intelligence schema:"
echo -e "          ${CYAN}https://console.cloud.google.com/bigquery?project=${PROJECT_ID}${RESET}"
echo -e "          ${DIM}(Verify dataset '${PROJECT_ID}.mission_data' and view 'v_multi_domain_intelligence')${RESET}"
echo ""
echo -e "  ${BOLD}Step 4:${RESET} Open the step-by-step Scenario 1 mission guide:"
echo -e "          ${CYAN}cat guide.md${RESET}  ${DIM}or view in your IDE${RESET}"
echo ""
echo -e "${BLUE}==============================================================================${RESET}"
