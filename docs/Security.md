# Security

## Dual-Template Model Armor Architecture
The platform enforces a zero-trust, defense-in-depth security posture utilizing Google Cloud Model Armor integrated into the agent lifecycle via the `after_model_callback`. It decouples inbound request protection from outbound response DLP.
- **Inbound Request Template** (`mission_intel_request_armor`): Evaluates Prompt Injection (PI) and Jailbreak attempts, enforcing safety filters (Hate Speech, Harassment) with `HIGH` confidence thresholds.
- **Outbound Response Template** (`mission_intel_response_armor`): Applies Cloud DLP Inspection and De-identification templates to intercept sensitive operational intelligence.
  - Custom regex templates flag standard PII alongside 10-digit Military Grid Reference System (MGRS) coordinates, UK/NATO national caveats (`UK EYES ONLY`), and tactical call signs (`SABRE-01`).
  - Flagged entities are deterministically redacted and replaced with tokenized InfoTypes such as `[CUSTOM_MGRS_COORDINATES]`.

## Zero-Trust Security & DevSecOps
The deployment assumes that even the reasoning model may exhibit probabilistic failures.
- **Machine-Speed Intercept**: Raw LLM output is intercepted before it reaches the UI. Model Armor's REST API (`sanitizeModelResponse`) scans and sanitizes the payload.
- **Local DLP Regex Fallback**: If the Model Armor endpoint times out or trips the circuit breaker, a hermetic Python regex fallback catches and redacts MGRS coordinates to `[REDACTED_MGRS_COORDINATE]`, guaranteeing zero operational data exfiltration under degraded network conditions.

## Human-in-the-Loop (HITL) Gateways
Autonomous tool execution is prevented from undertaking high-risk kinetic or cyber operations.
- The `evaluate_hitl_guardrail()` module detects triggers like `KINETIC_ENGAGEMENT` or `STRIKE ADVISORY`.
- When triggered, it forces the execution into a `HELD` state and overwrites the response to demand an explicit, non-delegable cryptographic command release token (`AUTH_<HASH>`) from the human analyst.

## Agent-to-Agent (A2A) Federation
The platform supports multi-national coalition scenarios (e.g. federating a UK Host Agent with a NATO MARCOM Partner Agent) using the Agent-to-Agent (A2A) JSON-RPC 2.0 protocol over the Gemini Enterprise Agent Gateway.
- **Boundary Federation**: Partner agents cannot query internal tools directly; they submit queries via `a2a.query` JSON-RPC. The Host Agent proxies the request, runs internal tools, and sanitizes the output.
- **NATO Caveat Sanitization**: Outbound A2A payloads automatically convert internal redactions to `[REDACTED_MGRS_COORDINATE_NATO_RELEASABLE]` and attach the mandatory `Demonstrator // REL TO NATO` classification caveat.
- **Kinetic Block**: Any A2A inbound request seeking kinetic action is blocked outright with `403 FORBIDDEN: SECURE_KINETIC_CONTROL_RESERVED`.

## IAM & MCP Governance
Authentication and Authorization are grounded in Agent Identities and Unified Access Policies (UAP).
- **Agent Identities (SPIFFE & mTLS)**: Reasoning Engine instances are assigned unique cryptographic identities (SVIDs). The agent leverages native SDK clients (e.g., `google-cloud-discoveryengine`) to automatically perform mTLS certificate exchange and bind the Agent's identity via Workload Identity for secure backend RAG querying. Access tokens are bound to the agent's private key using **DPoP** (Demonstrating Proof-of-Possession), nullifying token theft replay attacks.
- **Dual-Layer IAM Security for MCP**: Managed Model Context Protocol servers are protected by two gates:
  1. **The MCP Gate**: Principal must hold the `roles/mcp.toolUser` role.
  2. **The Service Gate**: Principal must hold the underlying GCP service role (e.g. `roles/bigquery.dataViewer`).
- **Cloud Identity SSO**: End-user authorization operates via Delegated OAuth tied to Cloud Identity / Google Workspace (integrated with 3P IdPs via SAML/OIDC), ensuring backend data queries execute under the end-user's native context and real-time ACLs.
