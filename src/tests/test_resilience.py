"""
Unit Tests for Resilience, Circuit Breakers, and Exponential Backoff.
"""

import unittest
from unittest.mock import MagicMock
from common.resilience import CircuitBreaker, CircuitBreakerOpenException, retry_with_backoff

class TestResilienceModule(unittest.TestCase):

    def test_retry_success_after_failure(self):
        mock_func = MagicMock(side_effect=[ValueError("Temporary network glitch"), "SUCCESS_RESULT"])
        
        decorated = retry_with_backoff(max_attempts=3, initial_delay=0.01, factor=1.5)(mock_func)
        result = decorated("arg1")
        
        self.assertEqual(result, "SUCCESS_RESULT")
        self.assertEqual(mock_func.call_count, 2)

    def test_circuit_breaker_trips_to_open_after_threshold(self):
        cb = CircuitBreaker(name="test_service", failure_threshold=3, recovery_timeout_sec=10.0)
        self.assertEqual(cb.state, "CLOSED")
        
        cb.record_failure()
        cb.record_failure()
        self.assertEqual(cb.state, "CLOSED")
        
        cb.record_failure()
        self.assertEqual(cb.state, "OPEN")
        self.assertFalse(cb.can_execute())

    def test_circuit_breaker_graceful_fallback(self):
        cb = CircuitBreaker(name="test_service", failure_threshold=1, recovery_timeout_sec=10.0)
        mock_failing_service = MagicMock(side_effect=RuntimeError("Service down"))
        fallback_handler = MagicMock(return_value="GRACEFUL_FALLBACK_INTELLIGENCE")
        
        decorated = retry_with_backoff(
            max_attempts=1,
            circuit_breaker=cb,
            fallback=fallback_handler
        )(mock_failing_service)
        
        result = decorated()
        self.assertEqual(result, "GRACEFUL_FALLBACK_INTELLIGENCE")
        self.assertEqual(cb.state, "OPEN")
        
        # Second call should immediately invoke fallback without calling the failing service
        result2 = decorated()
        self.assertEqual(result2, "GRACEFUL_FALLBACK_INTELLIGENCE")
        self.assertEqual(mock_failing_service.call_count, 1)

if __name__ == "__main__":
    unittest.main()
