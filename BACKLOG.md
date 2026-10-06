# Intelligence Agent: Backlog

- [x] **Offline Evaluation Testing**: Re-integrate and execute the offline evaluation tests (`run_offline_evaluation.py`) against the Golden Data Set as a separate CI/CD or testing exercise. Currently removed from the base deployment.
- [ ] **S1-P1 Fast Path Latency**: Investigate why `stream_query` execution in Vertex AI Reasoning Engine still incurs ~23s latency despite the `LlmResponse` short-circuit in `before_model_callback`. Test suite threshold is 10s.
