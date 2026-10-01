"""
Unit Tests for Vertex AI Context Caching Module.
"""

import os
import unittest
from unittest.mock import patch, MagicMock
from common.caching import (
    build_cached_mission_context,
    get_or_create_mission_cache,
    reset_active_cache,
    MINIMUM_CACHING_TOKEN_THRESHOLD
)

class TestCachingModule(unittest.TestCase):

    def setUp(self):
        reset_active_cache()

    def tearDown(self):
        reset_active_cache()

    def test_build_cached_mission_context_token_threshold(self):
        context = build_cached_mission_context()
        approx_tokens = len(context) // 4
        self.assertGreater(
            approx_tokens,
            MINIMUM_CACHING_TOKEN_THRESHOLD,
            f"Context token estimate ({approx_tokens}) must exceed minimum threshold ({MINIMUM_CACHING_TOKEN_THRESHOLD})."
        )
        self.assertIn("v_multi_domain_intelligence", context)
        self.assertIn("HUM-445", context)
        self.assertIn("HUM-454", context)

    def test_get_or_create_mission_cache_without_project(self):
        # Should safely return None when no project is provided or disabled
        old_project = os.environ.pop("PROJECT_ID", None)
        try:
            cache_ref = get_or_create_mission_cache(project_id=None)
            self.assertIsNone(cache_ref)
        finally:
            if old_project is not None:
                os.environ["PROJECT_ID"] = old_project

    def test_get_or_create_mission_cache_global_endpoint_routing(self):
        # Assert that gemini-3.8-flash automatically routes to global Vertex AI endpoint
        mock_vertexai = MagicMock()
        mock_preview = MagicMock()
        mock_caching = MagicMock()
        mock_preview.caching = mock_caching
        mock_cache = MagicMock()
        mock_cache.name = "cache_123"
        mock_cache.resource_name = "projects/test-proj/locations/global/cachedContents/cache_123"
        mock_caching.CachedContent.list.return_value = []
        mock_caching.CachedContent.create.return_value = mock_cache

        with patch.dict("sys.modules", {
            "vertexai": mock_vertexai,
            "vertexai.preview": mock_preview,
            "vertexai.preview.caching": mock_caching
        }):
            res = get_or_create_mission_cache(
                project_id="test-proj",
                location="us-central1", # explicitly pass regional, should route to global
                model_name="gemini-3.8-flash"
            )
            mock_vertexai.init.assert_called_with(project="test-proj", location="global")
            self.assertEqual(res, "projects/test-proj/locations/global/cachedContents/cache_123")

if __name__ == "__main__":
    unittest.main()
