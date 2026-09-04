"""Unit tests for Government of India Bhashini translation client and LLM fallback."""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.translation.bhashini import (
    is_bhashini_configured,
    translate_text,
    BHASHINI_LANG_MAP,
)


class TestBhashiniIntegration(unittest.TestCase):

    def test_unconfigured_credentials_returns_none(self):
        """When credentials are absent or default placeholders, translate_text should cleanly return None."""
        with patch.dict(os.environ, {"BHASHINI_API_KEY": "", "BHASHINI_USER_ID": ""}):
            self.assertFalse(is_bhashini_configured())
            result = translate_text("नमस्ते", "hi", "en")
            self.assertIsNone(result, "Unconfigured credentials should return None to trigger LLM fallback")

        with patch.dict(os.environ, {"BHASHINI_API_KEY": "your_bhashini_api_key_here", "BHASHINI_USER_ID": "your_bhashini_user_id_here"}):
            self.assertFalse(is_bhashini_configured())
            result = translate_text("नमस्ते", "hi", "en")
            self.assertIsNone(result, "Placeholder credentials should return None to trigger LLM fallback")

    def test_same_language_returns_original(self):
        """Translating to the same language should immediately return original string."""
        text = "Section 3(p) of the Patents Act"
        res = translate_text(text, "en", "en")
        self.assertEqual(res, text)

    def test_language_mappings_exist(self):
        """Core Indian official languages must exist in BHASHINI_LANG_MAP."""
        for code in ["en", "hi", "sa", "ta", "te", "bn", "mr", "gu"]:
            self.assertIn(code, BHASHINI_LANG_MAP)

    @patch("urllib.request.urlopen")
    def test_mock_successful_bhashini_response(self, mock_urlopen):
        """Simulate a valid 200 OK response from Bhashini Dhruva pipeline."""
        mock_response = MagicMock()
        mock_response.getcode.return_value = 200
        mock_response.read.return_value = b'''{
            "pipelineResponse": [
                {
                    "taskType": "translation",
                    "output": [
                        {
                            "source": "\xe0\xa4\xa8\xe0\xa4\xae\xe0\xa4\xb8\xe0\xa5\x8d\xe0\xa4\xa4\xe0\xa5\x87",
                            "target": "Hello and welcome"
                        }
                    ]
                }
            ]
        }'''
        mock_urlopen.return_value.__enter__.return_value = mock_response

        with patch.dict(os.environ, {"BHASHINI_API_KEY": "test_key_123", "BHASHINI_USER_ID": "test_user_456"}):
            self.assertTrue(is_bhashini_configured())
            result = translate_text("नमस्ते", "hi", "en")
            self.assertEqual(result, "Hello and welcome")

    @patch("urllib.request.urlopen")
    def test_mock_network_error_triggers_none_fallback(self, mock_urlopen):
        """Simulate an HTTP 503 error from Bhashini, ensuring fallback returns None."""
        import urllib.error
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="http://bhashini.mock", code=503, msg="Service Unavailable", hdrs={}, fp=None
        )

        with patch.dict(os.environ, {"BHASHINI_API_KEY": "test_key_123", "BHASHINI_USER_ID": "test_user_456"}):
            result = translate_text("नमस्ते", "hi", "en")
            self.assertIsNone(result, "HTTP error should return None to trigger LLM fallback")


if __name__ == "__main__":
    unittest.main(verbosity=2)
