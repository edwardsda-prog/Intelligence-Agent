#!/bin/bash
set -e
echo "1. Tearing down..."
./infrastructure/teardown.sh
echo "2. Setting up..."
./infrastructure/setup_infrastructure.sh
echo "3. Deploying Agent..."
python3 infrastructure/deploy_agent.py --test none
echo "4. Running E2E Tests..."
./src/tests/test_e2e.sh
