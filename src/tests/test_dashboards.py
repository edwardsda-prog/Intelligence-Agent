import unittest
import os
import json

class TestDashboardsAndTelemetry(unittest.TestCase):
    """
    Automated verification of Cloud Monitoring dashboard configs and telemetry seeding scripts.
    """

    def setUp(self):
        self.base_dir = os.path.join(os.path.dirname(__file__), "..")

    def test_dashboard_json_validity(self):
        """Verifies that all scenario dashboard JSON files are valid JSON and contain expected keys."""
        dashboards = [
            os.path.join(self.base_dir, "lab5", "code", "dashboard_observability.json"),
            os.path.join(self.base_dir, "lab5", "code", "dashboard_model_armor.json"),
        ]

        for dash_path in dashboards:
            self.assertTrue(os.path.exists(dash_path), f"Dashboard file missing: {dash_path}")
            with open(dash_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.assertIn("displayName", data, f"Missing 'displayName' in {dash_path}")
            self.assertIn("mosaicLayout", data, f"Missing 'mosaicLayout' in {dash_path}")
            self.assertGreater(len(data["mosaicLayout"]["tiles"]), 0, f"No tiles found in {dash_path}")

    def test_seeding_scripts_exist(self):
        """Verifies that telemetry seeding bash scripts exist and are executable."""
        scripts = [
            os.path.join(self.base_dir, "lab3", "code", "setup_telemetry.sh"),
            os.path.join(self.base_dir, "lab4", "code", "seed_security_telemetry.sh"),
            os.path.join(self.base_dir, "lab5", "code", "seed_rag_telemetry.sh"),
        ]

        for script_path in scripts:
            self.assertTrue(os.path.exists(script_path), f"Seeding script missing: {script_path}")
            self.assertTrue(os.access(script_path, os.X_OK), f"Seeding script not executable: {script_path}")

if __name__ == "__main__":
    unittest.main()
