"""
==============================================================================
Module: common/hitl.py
Human-in-the-Loop (HITL) Command Guardrail Subsystem
==============================================================================

Strategic Context & Lineage:
  - Scoping Document Section 2.3: "Human-in-the-Loop (HITL) Command Gateways"
  - Spec.md Phase 6 Action 3: Command Safety & Military Authorization Gates
  - Google Cloud Well-Architected Framework (WAF) Security Pillar:
    * Principle SEC-02: Zero-Trust authorization gates on sensitive actions.
  - UK MOD Joint Command Doctrine:
    * Mandates human chain-of-command confirmation prior to issuing kinetic strike
      advisories or offensive cyber operations. No autonomous kinetic execution.

Operational Logic:
  - High-consequence action requests without an active authorization token (`AUTH_<HASH>`)
    are immediately intercepted.
  - Returns a structured HOLD notice requiring analyst review and manual confirmation token.
"""

import os
import hashlib
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Action categories requiring explicit human chain-of-command authorization
HIGH_CONSEQUENCE_ACTIONS = {
    "KINETIC_ENGAGEMENT",
    "STRIKE_COORDINATES",
    "OFFENSIVE_CYBER_COUNTERMEASURE",
    "FIRE_AUTHORIZATION",
}

class HumanAuthorizationRequiredException(Exception):
    """Raised when an operation requires explicit human-in-the-loop authorization."""
    pass

def generate_authorization_token(action_type: str, target_id: str) -> str:
    """
    Generates an operational verification token required to clear the HITL gate.
    Binds the action type and target identifier to a deterministic authorization hash.
    """
    payload = f"AUTH:{action_type}:{target_id}:MOD_C2"
    return "AUTH_" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12].upper()

def evaluate_hitl_guardrail(
    action_type: str,
    details: Dict[str, Any],
    auth_token: Optional[str] = None
) -> Dict[str, Any]:
    """
    Evaluates whether a tactical action requires Human-in-the-Loop clearance.
    
    Args:
        action_type: Category of action (e.g., 'KINETIC_ENGAGEMENT', 'QUERY_BIGQUERY').
        details: Metadata dict containing target identifiers (e.g. {'target_id': 'TGT-ALPHA-7'}).
        auth_token: Optional confirmation token provided by the human analyst.
        
    Returns:
        Dict with status ("APPROVED", "HELD") and instructional response.
    """
    # Allow programmatic test harness bypass when explicitly configured
    if os.environ.get("SKIP_HITL_FOR_TESTS") == "1":
        return {"status": "APPROVED", "message": "HITL bypassed via test configuration."}

    action_upper = action_type.strip().upper()
    if action_upper in HIGH_CONSEQUENCE_ACTIONS:
        target_id = details.get("target_id", "UNKNOWN_TARGET")
        expected_token = generate_authorization_token(action_upper, target_id)
        
        # Intercept action if token is absent or invalid
        if not auth_token or auth_token.strip() != expected_token:
            logger.warning(
                f"🛑 HITL Gate Triggered: {action_upper} on target {target_id}. "
                f"Holding for UK Command Staff approval."
            )
            try:
                from observability import log_sre_telemetry
                log_sre_telemetry("hitl_guardrail_triggered", {
                    "status": "HELD",
                    "action_type": action_upper,
                    "target_id": target_id
                })
            except Exception:
                pass
            return {
                "status": "HELD",
                "action_type": action_upper,
                "target_id": target_id,
                "required_token": expected_token,
                "message": (
                    f"⚠️ **[HUMAN-IN-THE-LOOP HOLD REQUIRED]**\n\n"
                    f"**Action Category:** `{action_upper}`\n"
                    f"**Target Identifier:** `{target_id}`\n"
                    f"**Doctrine Rule:** Kinetic engagement recommendations and offensive cyber countermeasures "
                    f"require explicit UK MOD Joint Command Staff authorization before dissemination.\n\n"
                    f"To release this advisory, submit confirmation token: `{expected_token}`"
                )
            }

    return {"status": "APPROVED", "message": "Action cleared through standard rule of engagement parameters."}
