#!/bin/bash
set -e

# Master Provisioning Script for Intelligence-Agent

# Colors for output
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RESET='\033[0m'
BOLD='\033[1m'

echo -e "${CYAN}${BOLD}Starting Infrastructure Provisioning...${RESET}\n"

echo -e "${YELLOW}[1/5] Setting up base infrastructure and IAM...${RESET}"
./setup.sh

echo -e "\n${YELLOW}[2/5] Setting up BigQuery datasets and GCS buckets...${RESET}"
./setup_bigquery.sh

echo -e "\n${YELLOW}[3/5] Setting up Discovery Engine...${RESET}"
./setup_discovery_engine.sh

echo -e "\n${YELLOW}[4/5] Synchronizing Datastore with Unstructured Data...${RESET}"
./sync_datastore.sh

echo -e "\n${YELLOW}[5/5] Provisioning Model Armor and DLP templates...${RESET}"
./security/setup_model_armor.sh

echo -e "\n${GREEN}${BOLD}Provisioning Complete!${RESET}"
echo -e "You can now deploy the agent using:"
echo -e "${CYAN}python3 deploy_agent.py${RESET}"
