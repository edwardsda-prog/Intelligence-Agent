"""
Unit Tests for Vertex AI Reasoning Engine Telemetry Collection & Message Content Logging
========================================================================================
Validates that all agent packages (Scenarios 3, 5, 7) are configured so that BOTH checkboxes
under Vertex AI Reasoning Engine 'Telemetry Collection' are enabled:
  1. 'Enable instrumentation of OpenTelemetry traces, logs and metrics'
  2. 'Enable logging of prompt inputs and response outputs'
"""

import os
import json
import unittest
from dotenv import dotenv_values

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

AGENT_DIRS = [
    os.path.join(REPO_ROOT, "agent"),
]

REQUIRED_ENV_KEYS = {
    "GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY": "true",
    "OTEL_SEMCONV_STABILITY_OPT_IN": "gen_ai_latest_experimental",
    "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT": "EVENT_ONLY",
    "ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS": "true",
}


class TestTelemetryConfiguration(unittest.TestCase):
    """Verifies OpenTelemetry and GenAI message content logging configurations."""

    def test_agent_config_json_present_and_valid(self):
        """Verifies .agent_engine_config.json contains telemetry & prompt/response logging keys."""
        for agent_dir in AGENT_DIRS:
            config_path = os.path.join(agent_dir, ".agent_engine_config.json")
            self.assertTrue(
                os.path.exists(config_path),
                f"Missing .agent_engine_config.json in {agent_dir}"
            )
            with open(config_path, "r") as f:
                config = json.load(f)

            self.assertIn("env_vars", config, f"No env_vars in {config_path}")
            env_vars = config["env_vars"]

            # Checkbox 1: Enable instrumentation of OpenTelemetry traces, logs and metrics
            self.assertEqual(
                env_vars.get("GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY"),
                "true",
                f"Checkbox 1 failed: GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY not true in {config_path}"
            )

            # Checkbox 2: Enable logging of prompt inputs and response outputs
            self.assertIn(
                env_vars.get("OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT"),
                ["EVENT_ONLY", "SPAN_AND_EVENT", "true"],
                f"Checkbox 2 failed: OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT invalid in {config_path}"
            )
            self.assertEqual(
                env_vars.get("ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS"),
                "true",
                f"Checkbox 2 failed: ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS must be 'true' in {config_path}"
            )

    def test_agent_dotenv_present_and_valid(self):
        """Verifies .env is present in each agent package to prevent ADK CLI fallback to false."""
        for agent_dir in AGENT_DIRS:
            dotenv_path = os.path.join(agent_dir, ".env")
            self.assertTrue(
                os.path.exists(dotenv_path),
                f"Missing .env in {agent_dir}"
            )
            env_vars = dotenv_values(dotenv_path)

            # Checkbox 1: OpenTelemetry tracing
            self.assertEqual(
                env_vars.get("GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY"),
                "true",
                f"GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY not true in {dotenv_path}"
            )

            # Checkbox 2: Prompt inputs and response outputs logging
            self.assertIn(
                env_vars.get("OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT"),
                ["EVENT_ONLY", "SPAN_AND_EVENT", "true"],
                f"OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT invalid in {dotenv_path}"
            )
            self.assertEqual(
                env_vars.get("ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS"),
                "true",
                f"ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS must be 'true' in {dotenv_path}"
            )

    def test_adk_telemetry_context_resolution(self):
        """Verifies ADK telemetry context resolution properly maps to ContentCapturingMode.EVENT_ONLY."""
        from google.adk.telemetry.context import (
            _read_content_capturing_mode,
            _read_add_content_to_legacy_spans,
            ContentCapturingMode
        )

        original_content_env = os.environ.get("OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT")
        original_spans_env = os.environ.get("ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS")

        try:
            os.environ["OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT"] = "EVENT_ONLY"
            os.environ["ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS"] = "true"

            mode = _read_content_capturing_mode()
            self.assertEqual(mode, ContentCapturingMode.EVENT_ONLY)

            legacy_spans = _read_add_content_to_legacy_spans()
            self.assertTrue(legacy_spans)
        finally:
            if original_content_env is not None:
                os.environ["OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT"] = original_content_env
            else:
                os.environ.pop("OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT", None)

            if original_spans_env is not None:
                os.environ["ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS"] = original_spans_env
            else:
                os.environ.pop("ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS", None)

    def test_log_analysis_with_valid_telemetry_and_content(self):
        """Verifies log analyzer passes when OpenTelemetry traces/metrics and un-elided content exist."""
        from common.telemetry_log_analyzer import TelemetryLogAnalyzer

        sample_logs = [
            {
                "trace": "projects/mission-intel-project/traces/4bf92f3577b34da6a3ce929d0e0e4736",
                "spanId": "00f067aa0ba902b7",
                "resource": {"type": "aiplatform.googleapis.com/ReasoningEngine"},
                "jsonPayload": {
                    "attributes": {
                        "gen_ai.system": "google.adk",
                        "gen_ai.request.model": "gemini-3.8-flash",
                        "gen_ai.prompt": "Find the EW bearings associated with radar track TRK-901 in mission_data.",
                        "gen_ai.output.messages": "[{\"role\": \"assistant\", \"content\": \"Radar track TRK-901 correlates with EW bearing 042°...\"}]",
                        "gen_ai.usage.prompt_tokens": 1240,
                        "gen_ai.usage.completion_tokens": 320,
                        "gen_ai.latency_ms": 142.5
                    }
                }
            }
        ]

        analyzer = TelemetryLogAnalyzer()
        result = analyzer.analyze_logs(sample_logs)

        self.assertTrue(result.telemetry_instrumentation_working, "OpenTelemetry instrumentation check failed")
        self.assertTrue(result.content_logging_working, "Prompt/Response content logging check failed")
        self.assertTrue(result.all_checks_passed, "Overall telemetry log analysis failed")
        self.assertEqual(len(result.trace_ids_found), 1)
        self.assertEqual(len(result.prompts_captured), 1)
        self.assertEqual(len(result.responses_captured), 1)
        self.assertFalse(result.elided_content_detected)

    def test_log_analysis_with_custom_spans(self):
        """Verifies log analyzer captures custom spans model_armor_sanitization and auth_verification."""
        from common.telemetry_log_analyzer import TelemetryLogAnalyzer

        custom_logs = [
            {
                "trace": "projects/mission-intel-project/traces/4bf92f3577b34da6a3ce929d0e0e4737",
                "spanId": "00f067aa0ba902b8",
                "resource": {"type": "aiplatform.googleapis.com/ReasoningEngine"},
                "jsonPayload": {
                    "event_name": "model_armor_sanitization",
                    "attributes": {
                        "redacted": True,
                        "mgrs_count": 1,
                        "latency_ms": 12.5
                    }
                }
            },
            {
                "trace": "projects/mission-intel-project/traces/4bf92f3577b34da6a3ce929d0e0e4737",
                "spanId": "00f067aa0ba902b9",
                "resource": {"type": "aiplatform.googleapis.com/ReasoningEngine"},
                "jsonPayload": {
                    "span_name": "auth_verification",
                    "attributes": {
                        "user_id": "test_user"
                    }
                }
            }
        ]

        analyzer = TelemetryLogAnalyzer()
        result = analyzer.analyze_logs(custom_logs)

        self.assertIn("model_armor_sanitization", result.custom_spans_found)
        self.assertIn("auth_verification", result.custom_spans_found)

    def test_log_analysis_detects_elided_content_failure(self):
        """Verifies log analyzer flags failure when message content is elided (content logging disabled)."""
        from common.telemetry_log_analyzer import TelemetryLogAnalyzer

        elided_logs = [
            {
                "trace": "projects/mission-intel-project/traces/4bf92f3577b34da6a3ce929d0e0e4736",
                "spanId": "00f067aa0ba902b7",
                "resource": {"type": "aiplatform.googleapis.com/ReasoningEngine"},
                "jsonPayload": {
                    "attributes": {
                        "gen_ai.system": "google.adk",
                        "gen_ai.request.model": "gemini-3.8-flash",
                        "gen_ai.prompt": "<elided>",
                        "gen_ai.output.messages": "<elided>",
                        "gen_ai.usage.prompt_tokens": 1240,
                        "gen_ai.usage.completion_tokens": 320
                    }
                }
            }
        ]

        analyzer = TelemetryLogAnalyzer()
        result = analyzer.analyze_logs(elided_logs)

        self.assertTrue(result.telemetry_instrumentation_working, "OpenTelemetry traces should still be detected")
        self.assertFalse(result.content_logging_working, "Content logging should fail when elided")
        self.assertTrue(result.elided_content_detected, "Elided content must be detected")
        self.assertFalse(result.all_checks_passed, "Overall checks must fail when content is elided")
        self.assertTrue(any("elided" in reason.lower() for reason in result.failure_reasons))

    def test_log_analysis_detects_missing_telemetry_failure(self):
        """Verifies log analyzer flags failure when OpenTelemetry traces/spans/metrics are missing."""
        from common.telemetry_log_analyzer import TelemetryLogAnalyzer

        uninstrumented_logs = [
            {
                "resource": {"type": "aiplatform.googleapis.com/ReasoningEngine"},
                "jsonPayload": {
                    "message": "Simple unstructured log output without OpenTelemetry context"
                }
            }
        ]

        analyzer = TelemetryLogAnalyzer()
        result = analyzer.analyze_logs(uninstrumented_logs)

        self.assertFalse(result.telemetry_instrumentation_working)
        self.assertFalse(result.content_logging_working)
        self.assertFalse(result.all_checks_passed)

    def test_live_cloud_logging_telemetry(self):
        """Verifies live Cloud Logging entries for a deployed Reasoning Engine if REASONING_ENGINE_ID is set."""
        re_id = os.environ.get("REASONING_ENGINE_ID")
        project_id = os.environ.get("PROJECT_ID", "antig-dave")
        if not re_id:
            self.skipTest("REASONING_ENGINE_ID not set; skipping live cloud logging audit.")

        import subprocess
        from common.telemetry_log_analyzer import TelemetryLogAnalyzer

        cmd = [
            "gcloud", "logging", "read",
            f'resource.type="aiplatform.googleapis.com/ReasoningEngine" AND resource.labels.reasoning_engine_id="{re_id}"',
            f"--project={project_id}",
            "--limit=20",
            "--format=json"
        ]
        logs_raw = subprocess.check_output(cmd).decode("utf-8")
        logs = json.loads(logs_raw)
        analyzer = TelemetryLogAnalyzer()
        result = analyzer.analyze_logs(logs)

        self.assertTrue(result.telemetry_instrumentation_working, f"Live telemetry failed: {result.summary}")
        self.assertTrue(result.content_logging_working, f"Live content logging failed: {result.summary}")
        self.assertTrue(result.all_checks_passed, f"Live audit failed: {result.summary}")


if __name__ == "__main__":
    unittest.main()

