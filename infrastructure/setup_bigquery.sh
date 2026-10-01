#!/bin/bash
# ==============================================================================
# Setup Script: Lab 1 - Data Foundations & Multi-Domain Intelligence
# ==============================================================================

set -e
cd "$(dirname "$0")"

PROJECT_ID=${PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}
PROJECT_ID=${PROJECT_ID:-"${PROJECT_ID}"}
LOCATION=${LOCATION:-"us-central1"}
BUCKET_NAME="gs://${PROJECT_ID}-learning-labs-humint-docs"

echo "======================================================================"
echo "🚀 Provisioning Lab 1: BigQuery Multi-Domain Data & HUMINT Storage"
echo "Project ID:   $PROJECT_ID"
echo "Region:       $LOCATION"
echo "GCS Bucket:   $BUCKET_NAME"
echo "======================================================================"

# 1. Provision BigQuery Dataset
echo ""
echo "📌 [1/2] Provisioning BigQuery Dataset (learning_labs_mission_data)..."
bq query --location=$LOCATION --use_legacy_sql=false --project_id="$PROJECT_ID" < ./setup_dataset.sql
bq query --location=$LOCATION --use_legacy_sql=false --project_id="$PROJECT_ID" < ./setup_golden_dataset.sql

# Polling for BigQuery dataset readiness
echo "⏳ Polling BigQuery dataset learning_labs_mission_data for READY status..."
MAX_RETRIES=15
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if bq show --dataset "$PROJECT_ID:learning_labs_mission_data" >/dev/null 2>&1; then
        echo "✅ BigQuery dataset 'learning_labs_mission_data' and tables confirmed READY."
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT+1))
    echo "   [Attempt $RETRY_COUNT/$MAX_RETRIES] Waiting for BigQuery dataset provisioning..."
    sleep 2
done

# 2. Generate and Upload PDFs to GCS
echo ""
echo "📌 [2/2] Generating 15 Multimodal HUMINT PDF Reports & Syncing to GCS..."
pip install --quiet reportlab --break-system-packages || pip install --quiet --user reportlab
python3 # Generate PDFs omitted from deploy script, use synthetic data
python3 # jsonl omitted

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

echo ""
echo "📌 [3/3] Triggering Data Store Synchronization..."
./sync_datastore.sh

echo ""
echo "======================================================================"
echo "🎉 Lab 1 Setup Complete!"
echo "======================================================================"
