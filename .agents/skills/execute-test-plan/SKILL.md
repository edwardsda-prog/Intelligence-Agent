---
name: execute-test-plan
description: Execute the E2E Live Test Plan for the Mission Intel project to verify the multi-domain intelligence agentic ecosystem against both local SQLite and live Google Cloud infrastructure.
---

# Execute Mission Intel Test Plan

This skill automates the process of executing the Live E2E Test Plan for the Mission Intel project.

## Workflow Steps

1. **Verify Setup**: Ensure you are authenticated with Google Cloud (`gcloud auth login --update-adc` and `gcloud config set project <PROJECT_ID>`) and have the correct Python dependencies.
2. **Phase 0: Teardown & Clean-Slate Audit**: Run `bash lab0/code/teardown.sh` and verify all 7 resource categories return `CLEAN ✅ (Decommissioned)`. Purge local SQLite state (`rm -f lab2/mission_data.db`).
3. **Phase 1: Fail-Fast Unit & Schema Parity Gate**: Run `python3 -m unittest discover -s tests -p "test_*.py" -v` including `test_schema_parity.py` and `test_dashboards.py`.
4. **Phase 2: System Setup & Resource Naming Validation**: Run `bash lab0/code/setup.sh`. Ensure standard resource names are used (`mission_data`, `gs://${PROJECT_ID}-humint-docs`, `mission-intel-app`).
5. **Phase 3: Telemetry Seeding**: Execute telemetry seeding scripts:
   - `bash lab3/code/setup_telemetry.sh`
   - `bash lab4/code/seed_security_telemetry.sh`
   - `bash lab5/code/seed_rag_telemetry.sh`
6. **Phase 4: Hermetic & Live Execution**:
   - Run `cd tests && ./test_e2e.sh --mock` for offline validation.
   - Run `cd tests && ./test_e2e.sh --live` for full live cloud integration.
7. **Phase 5: Scorecard Review**: Inspect `tests/test_e2e_report.md` for 100% pass rates across all 39 test vectors.
