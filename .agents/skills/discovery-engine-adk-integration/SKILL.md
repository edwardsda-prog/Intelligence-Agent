---
name: discovery-engine-adk-integration
description: >-
  Technical runbook and pattern guide for integrating Discovery Engine unstructured OCR datastores,
  JSONL metadata ingestion, Gemini Enterprise engine patching, stale agent cleanup, and hybrid ADK 2.0 Reasoning Engine deployment.
---

# Discovery Engine & ADK 2.0 Hybrid Integration Runbook

This skill provides step-by-step procedures for provisioning Discovery Engine unstructured PDF datastores, executing JSONL document metadata imports, linking datastores to Gemini Enterprise applications, and deploying ADK 2.0 hybrid agents.

---

## 1. Datastore Provisioning & Multi-Datastore Engine Patching

### A. Create Unstructured OCR Datastore
```bash
TOKEN=$(gcloud auth print-access-token)
curl -X POST \
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
  }'
```

### B. Link Datastore to Engine (`updateMask=dataStoreIds`)
> [!IMPORTANT]
> When patching an existing Gemini Enterprise Engine, you MUST pass **ALL** active datastores in `dataStoreIds`. Passing only the new datastore will cause a `400 FAILED_PRECONDITION` error for removing required datastores.

```bash
curl -X PATCH \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -H "X-Goog-User-Project: ${PROJECT_ID}" \
  "https://discoveryengine.googleapis.com/v1alpha/projects/${PROJECT_ID}/locations/global/collections/default_collection/engines/${ENGINE_ID}?updateMask=dataStoreIds" \
  -d '{
      "dataStoreIds": ["rn-source-files_1790071861335", "'"${DATASTORE_ID}"'"]
  }'
```

---

## 2. JSONL Metadata Formatting & OCR Document Import

Discovery Engine unstructured imports require NDJSON / JSONL metadata format:

```json
{"id": "hum-445", "jsonData": "{\"title\": \"HUMINT Intelligence Report HUM-445\", \"file\": \"HUM-445_TGT-ALPHA-7.pdf\"}", "content": {"mimeType": "application/pdf", "uri": "gs://{PROJECT_ID}-humint-docs/HUM-445_TGT-ALPHA-7.pdf"}}
```

Trigger incremental import:
```bash
curl -X POST \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -H "X-Goog-User-Project: ${PROJECT_ID}" \
  "https://discoveryengine.googleapis.com/v1alpha/projects/${PROJECT_ID}/locations/global/collections/default_collection/dataStores/${DATASTORE_ID}/branches/0/documents:import" \
  -d '{
      "gcsSource": {
          "inputUris": ["gs://'"${PROJECT_ID}"'-humint-docs/documents.jsonl"]
      },
      "reconciliationMode": "INCREMENTAL"
  }'
```

---

## 3. Automated Agent Sync (Preventing NOT_FOUND UI Errors)

> [!IMPORTANT]
> A common point of failure is deploying a new Reasoning Engine ID via ADK but leaving the Gemini Enterprise UI (Discovery Engine) pointing to a stale, deleted backend, resulting in a `NOT_FOUND` stream error in the UI. 

To prevent this, you **MUST** automate the stale agent purge and the new `adkAgentDefinition` registration by injecting the following REST API sync logic directly into your deployment scripts (e.g., `setup_lab8.sh`), immediately following the `adk deploy` command:

```bash
# Sync active agent with Discovery Engine Agent Registry (prevent NOT_FOUND errors)
TOKEN=$(gcloud auth print-access-token)
ENGINE_ID="mission-intel-app"

echo "Purging stale Agent Registrations in Discovery Engine..."
for AGENT_ID_STALE in $(curl -s -H "Authorization: Bearer ${TOKEN}" -H "X-Goog-User-Project: ${PROJECT_ID}" "https://discoveryengine.googleapis.com/v1alpha/projects/${PROJECT_ID}/locations/global/collections/default_collection/engines/${ENGINE_ID}/assistants/default_assistant/agents" | grep -o '"name": "[^"]*"' | grep -o 'agents/[^"]*' | cut -d/ -f2); do
    if [ -n "$AGENT_ID_STALE" ]; then
        curl -s -X DELETE -H "Authorization: Bearer ${TOKEN}" -H "X-Goog-User-Project: ${PROJECT_ID}" "https://discoveryengine.googleapis.com/v1alpha/projects/${PROJECT_ID}/locations/global/collections/default_collection/engines/${ENGINE_ID}/assistants/default_assistant/agents/${AGENT_ID_STALE}"
    fi
done

echo "Registering active Reasoning Engine (${RE_ID}) with Gemini Enterprise UI..."
curl -s -X POST -H "Authorization: Bearer ${TOKEN}" -H "Content-Type: application/json" -H "X-Goog-User-Project: ${PROJECT_ID}" \
    "https://discoveryengine.googleapis.com/v1alpha/projects/${PROJECT_ID}/locations/global/collections/default_collection/engines/${ENGINE_ID}/assistants/default_assistant/agents?agentId=mission-intel-agent-live" \
    -d '{
        "displayName": "Mission Intel Agent",
        "description": "Mission Intel Hybrid Mission Intelligence Agent",
        "adkAgentDefinition": {
            "provisionedReasoningEngine": {
                "reasoningEngine": "'"${RE_ID}"'"
            }
        },
        "observabilityConfig": {
            "observabilityEnabled": true
        }
    }'
```
