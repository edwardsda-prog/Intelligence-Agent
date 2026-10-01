import unittest
import os
import sqlite3
import re

class TestSchemaParity(unittest.TestCase):
    """
    Verifies DDL schema parity between local SQLite database (Scenario 2)
    and BigQuery multi-domain tables/view (Scenario 1).
    """

    @classmethod
    def setUpClass(cls):
        # Initialize local SQLite DB if needed
        db_script = os.path.join(os.path.dirname(__file__), "..", "lab2", "code", "setup_local_db.py")
        db_path = os.path.join(os.path.dirname(__file__), "..", "lab2", "code", "mission_intel_local.db")
        if not os.path.exists(db_path):
            os.system(f"python3 {db_script}")
        cls.db_path = db_path

    def test_sqlite_tables_exist(self):
        """Verifies that all 6 core tables and 1 view exist in SQLite."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type IN ('table', 'view');")
        names = [row[0] for row in cursor.fetchall()]
        conn.close()

        expected_entities = [
            'radar_telemetry',
            'ew_intercepts',
            'satellite_recon',
            'cyber_threat_intel',
            'humint_reports',
            'friendly_assets',
            'v_multi_domain_intelligence'
        ]
        for entity in expected_entities:
            self.assertIn(entity, names, f"Missing entity '{entity}' in SQLite schema.")

    def test_view_columns_parity(self):
        """Verifies column parity for v_multi_domain_intelligence between SQLite and SQL definition."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(v_multi_domain_intelligence);")
        sqlite_cols = [row[1] for row in cursor.fetchall()]
        conn.close()

        expected_cols = [
            'track_id', 'target_id', 'radar_time', 'platform_type', 'radar_signature',
            'altitude_ft', 'velocity_knots', 'mgrs_coord', 'ew_id', 'emitter_type',
            'ew_bearing', 'signal_frequency_ghz', 'prf_khz', 'ew_threat_level',
            'image_id', 'sat_sensor', 'sat_detection', 'sat_confidence',
            'cyber_event_id', 'cyber_actor', 'cyber_target_system', 'cyber_status',
            'humint_id', 'humint_reliability', 'humint_content', 'friendly_unit',
            'friendly_callsign', 'friendly_perimeter'
        ]

        for col in expected_cols:
            self.assertIn(col, sqlite_cols, f"Column '{col}' missing from SQLite view v_multi_domain_intelligence.")

    def test_radar_telemetry_column_parity(self):
        """Verifies radar_telemetry columns match expected schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(radar_telemetry);")
        sqlite_cols = [row[1] for row in cursor.fetchall()]
        conn.close()

        expected_cols = [
            'track_id', 'timestamp', 'latitude', 'longitude', 'altitude_ft',
            'velocity_knots', 'bearing_degrees', 'heading_degrees', 'platform_type',
            'signature', 'target_id', 'mgrs_coord'
        ]
        for col in expected_cols:
            self.assertIn(col, sqlite_cols, f"Column '{col}' missing from radar_telemetry.")

if __name__ == "__main__":
    unittest.main()
