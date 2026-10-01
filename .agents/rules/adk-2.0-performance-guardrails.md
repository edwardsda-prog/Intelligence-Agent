---
trigger: always_on
description: Mandatory performance and latency guardrails for Google ADK 2.0 custom tool implementation and RAG retrieval.
---

# ADK 2.0 Performance & Latency Guardrails

When implementing custom Python function tools or RAG integration in Google Agent Developer Kit (ADK 2.0) agents, adhere to the following performance invariants to ensure sub-second tool execution and prevent ReAct loop timeouts:

1. **In-Memory Credential & Token Caching**:
   - NEVER invoke CLI subprocess calls (e.g. `subprocess.check_output(['gcloud', 'auth', 'print-access-token'])`) inside tool execution handlers. Subprocess spawns introduce 1.5–2.0s of process creation overhead per call.
   - Use in-memory cached Application Default Credentials (`google.auth.default()`) with token reuse.

2. **Single-Pass Multi-Document Retrieval (`pageSize`)**:
   - Set `pageSize` to match or exceed the total document count in the target corpus (e.g. `pageSize: 15`).
   - Restricting `pageSize` to small limits (e.g. `5`) forces Gemini LLMs to chain sequential ReAct tool calls across multiple turns, creating massive end-to-end latency (30+ seconds). Single-pass retrieval completes in sub-second speed (<0.3s).

3. **Omit Redundant Backend LLM Generation (`summarySpec`)**:
   - In Discovery Engine REST API payloads (`contentSearchSpec`), do NOT request `summarySpec` when the root ADK LLM agent (`gemini-3.8-flash` / `gemini-3.1-pro`) performs final synthesis. Backend summary generation adds ~3s of duplicate LLM processing.
   - Request extracted text snippets (`snippetSpec: {"returnSnippet": true}`) only.

4. **Clean String Formatting & Stripping**:
   - Clean HTML tags (`<b>`, `</b>`) and whitespace from extracted search snippets before returning them to the agent to minimize prompt token count.
