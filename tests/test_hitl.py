"""
Unit Tests for Human-in-the-Loop (HITL) Guardrails.
"""

import unittest
import os
from common.hitl import (
    evaluate_hitl_guardrail,
    generate_authorization_token,
    HIGH_CONSEQUENCE_ACTIONS
)

class TestHITLModule(unittest.TestCase):

    def setUp(self):
        # Ensure test bypass is disabled by default for explicit checking
        os.environ["SKIP_HITL_FOR_TESTS"] = "0"

    def test_standard_action_passes_without_hold(self):
        decision = evaluate_hitl_guardrail(
            action_type="QUERY_BIGQUERY_TELEMETRY",
            details={"target_id": "TGT-ALPHA-7"}
        )
        self.assertEqual(decision["status"], "APPROVED")

    def test_kinetic_strike_triggers_hold_without_token(self):
        decision = evaluate_hitl_guardrail(
            action_type="KINETIC_ENGAGEMENT",
            details={"target_id": "TGT-DELTA-9"}
        )
        self.assertEqual(decision["status"], "HELD")
        self.assertIn("HUMAN-IN-THE-LOOP HOLD REQUIRED", decision["message"])
        self.assertTrue(len(decision["required_token"]) > 0)

    def test_kinetic_strike_approved_with_valid_token(self):
        target_id = "TGT-DELTA-9"
        valid_token = generate_authorization_token("KINETIC_ENGAGEMENT", target_id)
        
        decision = evaluate_hitl_guardrail(
            action_type="KINETIC_ENGAGEMENT",
            details={"target_id": target_id},
            auth_token=valid_token
        )
        self.assertEqual(decision["status"], "APPROVED")

    def test_cyber_countermeasure_triggers_hold(self):
        decision = evaluate_hitl_guardrail(
            action_type="OFFENSIVE_CYBER_COUNTERMEASURE",
            details={"target_id": "TGT-ECHO-5"}
        )
        self.assertEqual(decision["status"], "HELD")

if __name__ == "__main__":
    unittest.main()
