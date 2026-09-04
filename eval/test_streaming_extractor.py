"""
Unit Test: IncrementalAnswerExtractor
Verifies real-time streaming answer extraction from LLM JSON tokens:
1. Filters out preamble, outer braces, `"answer": "` keys.
2. Unescapes JSON string characters (newlines, quotes, unicode) in real time.
3. Stops emitting when the answer string ends before citations.
"""

import sys
import unittest
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.api.routes import IncrementalAnswerExtractor


class TestIncrementalAnswerExtractor(unittest.TestCase):
    def test_clean_streaming_extraction(self):
        extractor = IncrementalAnswerExtractor()

        # Simulate LLM emitting tokens in small chunks
        raw_chunks = [
            '{\n  "answer": "Section 3(d) ',
            'of the Patents Act ',
            'prevents evergreening of patents.\\n\\n',
            'Key requirements include:\\n',
            '1. Enhanced therapeutic efficacy\\n',
            '2. Non-trivial modification",\n',
            '  "citations": [{"act_code": "PAT", "section": "Section 3(d)"}],\n',
            '  "confidence": "high"\n}'
        ]

        emitted_deltas = []
        for chunk in raw_chunks:
            delta = extractor.feed(chunk)
            if delta:
                emitted_deltas.append(delta)

        final_extracted = "".join(emitted_deltas)
        expected = (
            "Section 3(d) of the Patents Act prevents evergreening of patents.\n\n"
            "Key requirements include:\n"
            "1. Enhanced therapeutic efficacy\n"
            "2. Non-trivial modification"
        )
        self.assertEqual(final_extracted, expected)

    def test_no_answer_key_fallback(self):
        extractor = IncrementalAnswerExtractor()
        # Non-JSON or plain text stream
        raw_chunks = ["Hello ", "world, ", "this is ", "direct text."]
        emitted = []
        for chunk in raw_chunks:
            d = extractor.feed(chunk)
            if d:
                emitted.append(d)
        
        # When "answer": " is never found, extractor should not emit partial garbage
        self.assertEqual("".join(emitted), "")


if __name__ == "__main__":
    unittest.main()
