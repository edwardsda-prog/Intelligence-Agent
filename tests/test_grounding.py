"""
Unit Tests for Enterprise Grounding and Page-Level Citations.
"""

import unittest

def format_grounded_citation(doc_id: str, title: str, uri: str, page_number: int, segment_text: str) -> str:
    """Formats Discovery Engine extractive segment into structured markdown citation with page anchor."""
    clean_snippet = segment_text.replace("<b>", "").replace("</b>", "").strip()
    return (
        f"[{doc_id.upper()}, Page {page_number}: {title}]({uri}#page={page_number})\n"
        f"> Extractive Segment: \"{clean_snippet}\""
    )

class TestGroundingModule(unittest.TestCase):

    def test_page_level_citation_formatting(self):
        doc_id = "hum-448"
        title = "HUMINT Intelligence Report HUM-448"
        uri = "gs://test-bucket/HUM-448_TGT-DELTA-9.pdf"
        page = 2
        segment = "High-frequency radar emitter identified adjacent to submarine pen berth 4."
        
        citation = format_grounded_citation(doc_id, title, uri, page, segment)
        
        expected_link = "[HUM-448, Page 2: HUMINT Intelligence Report HUM-448](gs://test-bucket/HUM-448_TGT-DELTA-9.pdf#page=2)"
        self.assertIn(expected_link, citation)
        self.assertIn('> Extractive Segment: "High-frequency radar emitter', citation)

if __name__ == "__main__":
    unittest.main()
