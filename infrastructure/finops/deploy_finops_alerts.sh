#!/bin/bash
set -e

PROJECT_ID=$(gcloud config get-value project)
echo "Deploying FinOps Alert Policies to project: $PROJECT_ID"

echo "Deploying High Token Burn Alert..."
gcloud alpha monitoring policies create \
  --policy-from-file=alert_token_burn.json \
  --project=$PROJECT_ID

echo "Deploying Runaway Session Alert..."
gcloud alpha monitoring policies create \
  --policy-from-file=alert_runaway_session.json \
  --project=$PROJECT_ID

echo "FinOps Alert Policies deployed successfully."
