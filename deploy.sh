#!/bin/bash

# ==============================================================================
# Intelligence Agent: Master Deployment Script
# ==============================================================================
# This script is a convenient wrapper that calls the primary deployment logic
# located in the infrastructure folder. It handles the deployment of the Agent
# to Vertex AI Reasoning Engine and provisions the Cloud Monitoring Dashboards.

set -e

# Default to the 'quick' test suite if no arguments are provided.
# You can pass arguments like '--test demo' or '--skip-agent-deploy' directly.
ARGS="${@:---test quick}"

echo "🚀 Starting Intelligence Agent Deployment Wrapper..."
echo "Running: python3 infrastructure/deploy_agent.py $ARGS"
echo "----------------------------------------------------------------------"

# Execute the base infrastructure provisioning
echo "📌 Running Base Infrastructure Provisioning..."
./infrastructure/provision_all.sh

# Execute the core deployment python script
python3 infrastructure/deploy_agent.py $ARGS

echo "----------------------------------------------------------------------"
echo "✅ Deployment Wrapper Finished."
echo "Tip: Run './generate_scenario_data.py' to generate telemetry data for your dashboards."
