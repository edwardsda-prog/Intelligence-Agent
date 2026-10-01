---
name: gemini-3-8-flash-integration
description: Always enforce these rules when implementing or migrating to Gemini 3.8 Flash on the Agent Platform.
trigger: always_on
---

# Gemini 3.8 Flash Integration Rules

When writing Python code to invoke `gemini-3.8-flash` on the Gemini Enterprise Agent Platform, you MUST adhere to the following breaking changes:

1. **Enterprise Client Initialization**: You MUST use the `google.genai` SDK and initialize the client with `enterprise=True` and `location="global"`. Do NOT use `vertexai=True` or the legacy `vertexai` SDK.
   * *ADK Example*: `client_kwargs={"enterprise": True, "project": PROJECT_ID, "location": "global"}`
2. **Thinking Level Enum**: Never use the legacy integer `thinking_budget`. You MUST replace it with the string enum `thinking_level` set to `"HIGH"`, `"MEDIUM"`, or `"LOW"`.
