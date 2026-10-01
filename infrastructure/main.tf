variable "project_id" { type = string }
variable "region" {
  type    = string
  default = "us-central1"
}

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Enable required Google Cloud APIs for the scenarios
resource "google_project_service" "required_apis" {
  for_each = toset([
    "bigquery.googleapis.com",             # For Scenario 1 and MCP BigQuery integration
    "aiplatform.googleapis.com",           # For Agent Platform (formerly Vertex AI)
    "cloudaicompanion.googleapis.com",     # For Gemini Enterprise integration
    "dlp.googleapis.com",                  # For Sensitive Data Protection (DLP)
    "modelarmor.googleapis.com",            # For Model Armor (Scenario 4 Guardrails)
    "run.googleapis.com",                  # For Cloud Run MCP Server deployment
    "agentregistry.googleapis.com"         # For Agent Registry service resolution
  ])

  project = var.project_id
  service = each.key

  disable_on_destroy = false
}

# Create the BigQuery Dataset for Scenario 1
resource "google_bigquery_dataset" "mission_data" {
  dataset_id                  = "learning_lab_mission_data"
  friendly_name               = "Mission Intel Mission Data"
  description                 = "Dataset for multi-domain mission intelligence (radar telemetry, EW intercepts, satellite recon, cyber threat intel, HUMINT, and friendly blue force assets)"
  location                    = "US"
  
  depends_on = [
    google_project_service.required_apis["bigquery.googleapis.com"]
  ]
}
