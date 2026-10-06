#!/bin/bash
set -e
echo "1. Setting up infrastructure..."
./infrastructure/setup_infrastructure.sh

echo "2. Running E2E tests..."
./src/tests/test_e2e.sh
