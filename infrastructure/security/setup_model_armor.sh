#!/bin/bash
cd "$(dirname "$0")"
export PROJECT_ID=${PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}
export LOCATION=${LOCATION:-"us-central1"}

if [ -z "$PROJECT_ID" ]; then
    echo "Error: Please set PROJECT_ID or configure gcloud project."
    exit 1
fi

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

