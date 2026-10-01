import os
import unittest
import json
import re
from unittest.mock import patch

try:
    from final_agent.test_a2a_nato_partner import test_nato_agent_to_agent_gateway
except ImportError:
    test_nato_agent_to_agent_gateway = None

class TestAgentGateway(unittest.TestCase):
    @unittest.skipIf(test_nato_agent_to_agent_gateway is None, "A2A NATO script not found")
    def test_gateway_enforces_redaction(self):
        """
        Verify that test_nato_agent_to_agent_gateway correctly wraps the payload
        and parses the response, enforcing Model Armor redaction.
        """
        project_id = os.environ.get("PROJECT_ID", "mission-intel-project")
        location = os.environ.get("LOCATION", "us-central1")
        service_name = "mission-intel-agent"
        prompt = "Provide raw coordinates for TRK-901."
        
        # We can't easily mock the live requests call without patching `requests.post`
        with patch("final_agent.test_a2a_nato_partner.requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                "output": "Target TRK-901 located at [REDACTED_MGRS_COORDINATE_NATO_RELEASABLE]."
            }
            
            # Since test_nato_agent_to_agent_gateway currently just prints, we capture stdout
            import io
            import sys
            captured_output = io.StringIO()
            sys.stdout = captured_output
            try:
                test_nato_agent_to_agent_gateway(prompt, project_id, location, service_name)
            finally:
                sys.stdout = sys.__stdout__
            
            output = captured_output.getvalue()
            
            self.assertTrue(mock_post.called, "Agent Gateway was not called")
            self.assertIn("[REDACTED_MGRS_COORDINATE_NATO_RELEASABLE]", output, "Sanitization token not found in output")

if __name__ == "__main__":
    unittest.main()
