"""
==============================================================================
Module: common/telemetry_log_analyzer.py
Telemetry Log Analyzer for Google Cloud Vertex AI & OpenTelemetry GenAI Conventions
==============================================================================

Strategic Context & Lineage:
  - Scoping Document Section 2.4: "Observability, OpenTelemetry & Logging Auditing"
  - Spec.md Phase 4 & Phase 7: Vertex AI Reasoning Engine Telemetry Validation
  - Google Cloud Well-Architected Framework (WAF) Operational Excellence Pillar:
    * Principle OPS-01: Capture distributed trace context and tool latency metrics.
    * Principle OPS-02: Ensure end-to-end prompt/response transparency without data loss.
    * Principle OPS-03: Automated log auditing to detect instrumentation and content degradation.

Observability Invariants:
  1. OpenTelemetry instrumentation (traces, spans, and GenAI metric conventions) is active.
     Configured via GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=true.
  2. Prompt inputs and response outputs logging is active (un-redacted, non-elided payloads).
     Configured via OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=EVENT_ONLY.
"""

import re
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

ELIDED_PLACEHOLDER = "<elided>"


@dataclass
class TelemetryAnalysisResult:
    """Detailed scorecard for OpenTelemetry and Prompt/Response log analysis."""
    # Checkbox 1: Instrumentation of OpenTelemetry traces, logs and metrics
    telemetry_instrumentation_working: bool = False
    trace_ids_found: List[str] = field(default_factory=list)
    span_ids_found: List[str] = field(default_factory=list)
    gen_ai_system_found: Optional[str] = None
    metrics_captured: Dict[str, Any] = field(default_factory=dict)
    
    # Checkbox 2: Logging of prompt inputs and response outputs
    content_logging_working: bool = False
    prompts_captured: List[str] = field(default_factory=list)
    responses_captured: List[str] = field(default_factory=list)
    elided_content_detected: bool = False
    
    # Audit trail
    total_entries_inspected: int = 0
    failure_reasons: List[str] = field(default_factory=list)
    summary: str = ""

    @property
    def all_checks_passed(self) -> bool:
        return self.telemetry_instrumentation_working and self.content_logging_working


class TelemetryLogAnalyzer:
    """Analyzes log entries from Vertex AI Reasoning Engine executions."""

    def __init__(self):
        pass

    def analyze_logs(self, log_entries: List[Dict[str, Any]]) -> TelemetryAnalysisResult:
        """Parses a list of log records (or Cloud Logging JSON entries) and validates telemetry."""
        result = TelemetryAnalysisResult(total_entries_inspected=len(log_entries))

        if not log_entries:
            result.failure_reasons.append("Log entry list is empty. No telemetry was emitted.")
            result.summary = "FAIL: Zero log entries inspected."
            return result

        for entry in log_entries:
            self._inspect_entry(entry, result)

        # Evaluate Checkbox 1: OpenTelemetry Traces, Logs & Metrics
        has_traces = len(result.trace_ids_found) > 0
        has_spans = len(result.span_ids_found) > 0
        has_system = result.gen_ai_system_found is not None
        has_metrics = len(result.metrics_captured) > 0

        if has_traces and has_spans and has_system:
            result.telemetry_instrumentation_working = True
        else:
            missing_parts = []
            if not has_traces: missing_parts.append("Trace IDs")
            if not has_spans: missing_parts.append("Span IDs")
            if not has_system: missing_parts.append("gen_ai.system")
            result.failure_reasons.append(
                f"OpenTelemetry instrumentation incomplete: Missing {', '.join(missing_parts)}"
            )

        # Evaluate Checkbox 2: Logging of Prompt Inputs and Response Outputs
        has_prompts = len(result.prompts_captured) > 0
        has_responses = len(result.responses_captured) > 0

        if result.elided_content_detected:
            result.failure_reasons.append(
                "Prompt/Response logging failed: Found '<elided>' placeholder in message payload. "
                "Ensure OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT and ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS are enabled."
            )

        if has_prompts and has_responses and not result.elided_content_detected:
            result.content_logging_working = True
        else:
            if not has_prompts:
                result.failure_reasons.append("No prompt input content captured in log entries.")
            if not has_responses:
                result.failure_reasons.append("No model response output content captured in log entries.")

        # Build human-readable summary
        if result.all_checks_passed:
            result.summary = (
                f"PASS ✅: Both OpenTelemetry instrumentation ({len(result.trace_ids_found)} traces, "
                f"{len(result.span_ids_found)} spans) and Prompt/Response logging "
                f"({len(result.prompts_captured)} prompts, {len(result.responses_captured)} responses) "
                f"are actively working."
            )
        else:
            result.summary = f"FAIL ❌: {'; '.join(result.failure_reasons)}"

        return result

    def _inspect_entry(self, entry: Dict[str, Any], result: TelemetryAnalysisResult) -> None:
        """Inspects an individual log entry for trace context, metrics, and message bodies."""
        # 1. Trace and Span extraction (Cloud Logging format and OpenTelemetry standard)
        trace_id = (
            entry.get("trace") or 
            entry.get("trace_id") or 
            entry.get("logging.googleapis.com/trace") or
            entry.get("attributes", {}).get("trace_id")
        )
        if trace_id:
            # Clean up projects/xxx/traces/yyy format if present
            clean_trace = trace_id.split("/")[-1]
            if clean_trace and clean_trace not in result.trace_ids_found:
                result.trace_ids_found.append(clean_trace)

        span_id = (
            entry.get("spanId") or 
            entry.get("span_id") or 
            entry.get("logging.googleapis.com/spanId") or
            entry.get("attributes", {}).get("span_id")
        )
        if span_id and span_id not in result.span_ids_found:
            result.span_ids_found.append(str(span_id))

        # 2. Extract payload attributes (handling jsonPayload, labels, otel, attributes, or root level)
        payload = entry.get("jsonPayload", entry)
        labels = entry.get("labels", {})
        otel_scope = entry.get("otel", {}).get("scope", {}).get("name")
        otel_sdk = entry.get("otel", {}).get("resource", {}).get("attributes", {}).get("telemetry.sdk.name")
        attrs = {}
        if isinstance(payload, dict):
            attrs.update(payload)
            if "attributes" in payload and isinstance(payload["attributes"], dict):
                attrs.update(payload["attributes"])
        if isinstance(labels, dict):
            attrs.update(labels)

        # Check gen_ai.system or otel scope
        system = (
            attrs.get("gen_ai.system") or 
            attrs.get("gen_ai.agent.name") or
            otel_scope or
            otel_sdk or
            payload.get("gen_ai_system")
        )
        if system:
            result.gen_ai_system_found = str(system)

        # Check GenAI metrics (token usage, latencies)
        prompt_tokens = (
            attrs.get("gen_ai.usage.input_tokens") or 
            attrs.get("gen_ai.usage.prompt_tokens") or 
            attrs.get("gen_ai_usage_prompt_tokens")
        )
        completion_tokens = (
            attrs.get("gen_ai.usage.output_tokens") or 
            attrs.get("gen_ai.usage.completion_tokens") or 
            attrs.get("gen_ai_usage_completion_tokens")
        )
        latency = attrs.get("gen_ai.latency_ms") or attrs.get("latency_ms")

        if prompt_tokens is not None:
            result.metrics_captured["prompt_tokens"] = prompt_tokens
        if completion_tokens is not None:
            result.metrics_captured["completion_tokens"] = completion_tokens
        if latency is not None:
            result.metrics_captured["latency_ms"] = latency

        # 3. Check Prompt Inputs
        prompt_content = (
            attrs.get("gen_ai.prompt") or 
            attrs.get("user_prompt") or 
            attrs.get("gen_ai.input.messages")
        )
        # Check stable semconv event body: gen_ai.user.message
        if not prompt_content and payload.get("event_name") == "gen_ai.user.message":
            prompt_content = payload.get("body", {}).get("content")

        if prompt_content is not None:
            prompt_str = str(prompt_content).strip()
            if prompt_str == ELIDED_PLACEHOLDER:
                result.elided_content_detected = True
            elif prompt_str:
                result.prompts_captured.append(prompt_str)

        # 4. Check Response Outputs
        response_content = (
            attrs.get("gen_ai.output.messages") or 
            attrs.get("model_response") or 
            attrs.get("response")
        )
        # Check stable semconv event body: gen_ai.choice
        if not response_content and payload.get("event_name") == "gen_ai.choice":
            response_content = payload.get("body", {}).get("content")

        if response_content is not None:
            resp_str = str(response_content).strip()
            if resp_str == ELIDED_PLACEHOLDER:
                result.elided_content_detected = True
            elif resp_str:
                result.responses_captured.append(resp_str)


def analyze_cloud_logging_json(json_str_or_data: Any) -> TelemetryAnalysisResult:
    """Helper function to analyze raw Cloud Logging JSON output."""
    if isinstance(json_str_or_data, str):
        try:
            data = json.loads(json_str_or_data)
        except Exception as e:
            res = TelemetryAnalysisResult()
            res.failure_reasons.append(f"Failed to parse JSON string: {e}")
            res.summary = f"FAIL ❌: Invalid JSON: {e}"
            return res
    else:
        data = json_str_or_data

    entries = data if isinstance(data, list) else [data]
    analyzer = TelemetryLogAnalyzer()
    return analyzer.analyze_logs(entries)
