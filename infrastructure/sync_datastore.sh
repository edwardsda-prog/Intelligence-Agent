#!/bin/bash
# ==============================================================================
# Script: sync_datastore.sh
# Purpose: Synchronizes GCS PDFs into the Discovery Engine Datastore if it exists.
# ==============================================================================

set -e

PROJECT_ID=${PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}
PROJECT_ID=${PROJECT_ID:-"${PROJECT_ID}"}
LOCATION=${LOCATION:-"us-central1"}
BUCKET_NAME="gs://${PROJECT_ID}-humint-docs"

echo "======================================================================"
echo "🔄 Synchronizing GCS documents to Discovery Engine..."
echo "Project ID:   $PROJECT_ID"
echo "GCS Bucket:   $BUCKET_NAME"
echo "======================================================================"

TOKEN=$(gcloud auth print-access-token)

# Discover existing active datastore
EXISTING_DS=$(curl -s -H "Authorization: Bearer ${TOKEN}" -H "X-Goog-User-Project: ${PROJECT_ID}" "https://discoveryengine.googleapis.com/v1alpha/projects/${PROJECT_ID}/locations/global/collections/default_collection/dataStores" | python3 -c "import sys, json; data = json.load(sys.stdin); res = [ds.get('name', '').split('/')[-1] for ds in data.get('dataStores', []) if ds.get('name', '').split('/')[-1].startswith('humint-pdf-datastore')]; print(res[0] if res else '')")

if [ -n "$EXISTING_DS" ]; then
    DATASTORE_ID="$EXISTING_DS"
    echo "📌 Found active Discovery Engine DataStore: $DATASTORE_ID"
    
    echo "📌 Importing PDF Documents into Datastore with OCR via JSONL..."
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
    
    echo "✅ Datastore synchronization triggered successfully."
else
    echo "ℹ️ No active Discovery Engine DataStore found starting with 'humint-pdf-datastore'. Skipping sync."
    echo "   (This is expected if Scenario 5 has not been deployed yet)."
fi
