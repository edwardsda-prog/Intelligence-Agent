#!/bin/bash
# ==============================================================================
# Intelligence Agent: Offline Evaluation Trigger
# ==============================================================================
#
# This script is a wrapper to manually trigger the LLM-as-a-Judge offline
# evaluation against the Golden Data Set. It sets up the required environment
# variables and authentication before invoking the Python test suite.
#
# Usage:
#   ./evaluate.sh
#

set -e
cd "$(dirname "$0")"

echo "======================================================================"
echo "🧪 Intelligence Agent: Offline Evaluation"
echo "======================================================================"

# 1. Discover active project
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

# 2. Check for ADK installation
if ! command -v adk &> /dev/null; then
    echo "⚠️  Google Agent Developer Kit (ADK) CLI not found in PATH."
    echo "Please ensure you have installed it: pip install google-adk"
    # We don't exit here strictly, as the python script might be using a venv
fi

# 3. Authenticate
echo "🔑 Verifying credentials..."
if ! gcloud auth print-access-token &> /dev/null; then
     echo "❌ You must be logged in. Please run: gcloud auth login"
     exit 1
fi

export PROJECT_ID="$PROJECT_ID"
export LOCATION="$LOCATION"

# 4. Run Evaluation
echo "🚀 Starting 7 Quality Dimensions Evaluation..."
echo "----------------------------------------------------------------------"
python3 ../src/tests/run_offline_evaluation.py

echo "----------------------------------------------------------------------"
echo "✅ Evaluation Complete."
echo "======================================================================"
