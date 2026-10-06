import re
import os

base_dir = "/usr/local/google/home/edwardsda/Documents/Intelligence-Agent/infrastructure"

def read_file(name):
    with open(os.path.join(base_dir, name), "r") as f:
        return f.read()

setup_sh = read_file("setup.sh")
setup_bq = read_file("setup_bigquery.sh")
setup_de = read_file("setup_discovery_engine.sh")
sync_ds = read_file("sync_datastore.sh")
setup_ma = read_file("security/setup_model_armor.sh")

out = []
out.append("#!/bin/bash")
out.append("# ==============================================================================")
out.append("# Unified Mission Intel Infrastructure Provisioning Script")
out.append("# ==============================================================================")
out.append("set -e")
out.append("SCRIPT_DIR=\"$(cd \"$(dirname \"${BASH_SOURCE[0]}\")\" && pwd)\"")
out.append("cd \"$SCRIPT_DIR\"")
out.append("if [ -d \"/home/aguser/Documents/Research/bin\" ]; then export PATH=\"/home/aguser/Documents/Research/bin:$PATH\"; fi")

# Extract section 1-4 from setup.sh
setup_sh_lines = setup_sh.split("\n")
# Extract everything from setup.sh after "set -e" to the end of Section 4
start_idx = setup_sh_lines.index("set -e") + 1
end_idx = 0
for i, l in enumerate(setup_sh_lines):
    if "Gemini Enterprise Engine Provisioning" in l:
        end_idx = i - 2
        break

out.extend(setup_sh_lines[start_idx:end_idx])

# Extract BigQuery
out.append("\n# ==============================================================================")
out.append("# BigQuery Dataset Provisioning")
out.append("# ==============================================================================")
bq_lines = setup_bq.split("\n")
bq_start = bq_lines.index("# 1. Provision BigQuery Dataset")
bq_end = bq_lines.index("# 2. Generate and Upload PDFs to GCS")
out.extend(bq_lines[bq_start:bq_end])

# Extract PDF sync
out.append("\n# ==============================================================================")
out.append("# PDF Upload & Cloud Storage Sync")
out.append("# ==============================================================================")
pdf_start = bq_lines.index("# 2. Generate and Upload PDFs to GCS")
pdf_end = bq_lines.index("echo \"📌 [3/3] Triggering Data Store Synchronization...\"") - 1
out.extend(bq_lines[pdf_start:pdf_end])

# Extract Gemini Enterprise App and Datastore
out.append("\n# ==============================================================================")
out.append("# Discovery Engine & Gemini Enterprise App Provisioning")
out.append("# ==============================================================================")
de_lines = setup_de.split("\n")
de_ds_setup_start = de_lines.index("# Discover existing active datastore or generate fresh ID")
de_ds_setup_end = de_lines.index("# 1. Verify / Generate PDF Documents")
out.extend(de_lines[de_ds_setup_start:de_ds_setup_end])

de_ds_link_start = de_lines.index("# 3. Create Discovery Engine Unstructured Datastore & Link to Gemini Enterprise App")
de_ds_link_end = de_lines.index("# 4. Trigger OCR Document Import via JSONL")
out.extend(de_lines[de_ds_link_start:de_ds_link_end])

# OCR Import
out.append("\n# ==============================================================================")
out.append("# Trigger OCR Document Import")
out.append("# ==============================================================================")
ocr_start = de_lines.index("# 4. Trigger OCR Document Import via JSONL")
ocr_end = de_lines.index("# 5. Disable Google Search Grounding for Security")
out.extend(de_lines[ocr_start:ocr_end])

# Disable search grounding
out.append("\n# ==============================================================================")
out.append("# Security: Disable Search Grounding")
out.append("# ==============================================================================")
grounding_start = de_lines.index("# 5. Disable Google Search Grounding for Security")
grounding_end = de_lines.index("# 6. Deploy Hybrid Reasoning Engine & Register in Gemini Enterprise")
out.extend(de_lines[grounding_start:grounding_end])

# Model Armor
out.append("\n# ==============================================================================")
out.append("# DLP and Model Armor Templates")
out.append("# ==============================================================================")
ma_lines = setup_ma.split("\n")
ma_start = ma_lines.index("echo \"Setting up Data Loss Prevention (DLP) Templates for Model Armor in project $PROJECT_ID (location: $LOCATION)...\"")
out.extend(ma_lines[ma_start:])

out.append("\n")
out.append("echo \"======================================================================\"")
out.append("echo \"🎉 INFRASTRUCTURE PROVISIONING COMPLETE!\"")
out.append("echo \"======================================================================\"")

with open(os.path.join(base_dir, "setup_infrastructure.sh"), "w") as f:
    f.write("\n".join(out) + "\n")

