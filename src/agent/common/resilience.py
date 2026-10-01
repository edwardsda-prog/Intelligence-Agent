"""
==============================================================================
Module: common/resilience.py
Mission Intelligence Agent Resilience & Fault Tolerance Subsystem
==============================================================================

Strategic Context & Lineage:
  - Scoping Document Section 2.3: "Multi-Tool Resilience & Circuit Breakers"
  - Spec.md Phase 3 & Phase 4: MCP and Unstructured Tool Resilience
  - Google Cloud Well-Architected Framework (WAF) Reliability Pillar:
    * Principle REL-01: Prevent cascading failures using Circuit Breakers.
    * Principle REL-02: Implement exponential backoff with jitter on transient faults.
    * Principle REL-03: Graceful degradation (return cached/fallback telemetry).

Environment:
  - Designed for secure operations across secure enterprise cloud
    and Google Cloud Platform environments.
"""

import time
import functools
import logging
from typing import Callable, Any, Optional

logger = logging.getLogger(__name__)

class CircuitBreakerOpenException(Exception):
    """Raised when an operation is attempted while the circuit breaker is in OPEN state."""
    pass

class CircuitBreaker:
    """
    Finite State Machine implementing the Circuit Breaker pattern.
    
    States:
      - CLOSED: Normal operational state. Requests pass through to the underlying service.
      - OPEN: Service failure threshold (default: 3) exceeded. Calls fail fast or route to
              graceful fallback without placing load on the degraded dependency.
      - HALF_OPEN: Cooldown interval (default: 30s) elapsed. A single trial request is permitted
                   to test whether the downstream service has recovered.
    """
    def __init__(self, name: str, failure_threshold: int = 3, recovery_timeout_sec: float = 30.0):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout_sec = recovery_timeout_sec
        self.state = "CLOSED"
        self.failure_count = 0
        self.last_failure_time = 0.0

    def can_execute(self) -> bool:
        """Determines whether a call should be allowed through based on current breaker state."""
        if self.state == "CLOSED":
            return True
        if self.state == "OPEN":
            if time.time() - self.last_failure_time >= self.recovery_timeout_sec:
                logger.warning(
                    f"⚠️ Circuit Breaker '{self.name}' transitioning to HALF_OPEN (probing downstream recovery)."
                )
                self.state = "HALF_OPEN"
                return True
            return False
        if self.state == "HALF_OPEN":
            return True
        return False

    def record_success(self):
        """Records a successful invocation, resetting the breaker back to CLOSED state."""
        if self.state in ("HALF_OPEN", "OPEN"):
            logger.info(f"✅ Circuit Breaker '{self.name}' confirmed recovered. State reset to CLOSED.")
        self.state = "CLOSED"
        self.failure_count = 0

    def record_failure(self):
        """Records a failure event. Trips breaker to OPEN when threshold is met."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.error(
                f"🛑 Circuit Breaker '{self.name}' TRIPPED to OPEN after {self.failure_count} consecutive failures. "
                f"Graceful degradation active for {self.recovery_timeout_sec}s cooldown."
            )

def retry_with_backoff(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    factor: float = 2.0,
    circuit_breaker: Optional[CircuitBreaker] = None,
    fallback: Optional[Callable[..., Any]] = None,
):
    """
    Decorator implementing exponential backoff retries with circuit breaker coordination.
    
    Args:
        max_attempts: Maximum retry invocations before tripping failure (default: 3).
        initial_delay: Initial sleep duration in seconds (default: 1.0s).
        factor: Multiplier applied per retry (e.g. 1.0s -> 2.0s -> 4.0s).
        circuit_breaker: Optional CircuitBreaker instance tracking endpoint health.
        fallback: Optional graceful degradation callable invoked if all retries fail or circuit is open.
    """
    def decorator(func: Callable[..., Any]):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 1. Fast-fail if circuit breaker is already OPEN
            if circuit_breaker and not circuit_breaker.can_execute():
                logger.warning(f"Circuit breaker '{circuit_breaker.name}' is OPEN. Invoking fallback handler.")
                if fallback:
                    return fallback(*args, **kwargs)
                raise CircuitBreakerOpenException(
                    f"Service '{circuit_breaker.name}' is temporarily unavailable (circuit OPEN)."
                )

            delay = initial_delay
            last_err = None
            func_name = getattr(func, "__name__", str(func))

            # 2. Execute attempts with exponential backoff
            for attempt in range(1, max_attempts + 1):
                try:
                    result = func(*args, **kwargs)
                    if circuit_breaker:
                        circuit_breaker.record_success()
                    return result
                except Exception as err:
                    last_err = err
                    logger.warning(
                        f"Attempt {attempt}/{max_attempts} failed for '{func_name}': {err}. "
                        f"{'Retrying in ' + str(delay) + 's...' if attempt < max_attempts else 'Retries exhausted.'}"
                    )
                    if attempt < max_attempts:
                        time.sleep(delay)
                        delay *= factor

            # 3. Trip circuit breaker on failure exhaustion
            if circuit_breaker:
                circuit_breaker.record_failure()

            # 4. Invoke fallback if provided, else propagate original exception
            if fallback:
                logger.info(f"Invoking graceful degradation fallback for '{func_name}'.")
                return fallback(*args, **kwargs)

            raise last_err
        return wrapper
    return decorator
