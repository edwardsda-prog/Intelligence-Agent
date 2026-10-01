# Automated Test Suite: Learning Lab Mission Intelligence

This directory contains the automated test suite that verifies the reliability, security, and functionality of the Agentic AI labs.

## Automated E2E Runner
The primary entrypoint for running tests is `test_e2e.sh`. 
When running tests, ensure you are in the root directory of the repository or execute it directly from the `tests/` folder.

```bash
# Run 39 tests hermetically (offline) without live GCP quotas
./tests/test_e2e.sh --mock

# Run only the 17 unit tests
./tests/test_e2e.sh --unit-only

# Run live integration against actual Google Cloud infrastructure
./tests/test_e2e.sh --live
```

## Test Files & Coverage

| File | Type | Coverage |
| :--- | :--- | :--- |
| `test_all_labs_prompts.py` | Integration | End-to-end execution of the 18 master prompts and 4 SQL queries spanning Labs 1-7. Validates cross-sensor correlation and output OPSEC redactions. |
| `test_caching.py` | Unit | Verifies Context Caching token calculation, TTL routing, and cache fallbacks. |
| `test_grounding.py` | Unit | Verifies extractive segment parsing and `#page=N` Markdown deep link generation for PDF reporting. |
| `test_hitl.py` | Unit | Verifies Human-in-the-Loop (HITL) cryptographic gating (`AUTH_<HASH>`) for kinetic/cyber strike intents. |
| `test_resilience.py` | Unit | Verifies the 3-state Circuit Breaker (`CLOSED`, `OPEN`, `HALF_OPEN`) and exponential backoff retry mechanics. |
| `test_telemetry.py` | Unit | Validates OpenTelemetry trace contexts, `gen_ai.*` semantic conventions, and missing-payload detection. |
