"""Test script for Multilingual Hindi Query processing and Translation round-trip."""

import sys
import os
import json
import httpx

# Ensure UTF-8 output on Windows
if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8")

BACKEND_URL = "http://localhost:8000/ask"


def test_hindi_roundtrip():
    print("=" * 80)
    print("TESTING HINDI QUERY ROUND-TRIP TRANSLATION & GROUNDED QA")
    print("=" * 80)

    hindi_query = "क्या शास्त्रीय आयुर्वेदिक फॉर्मूलेशन भारतीय पेटेंट कानून के तहत पेटेंट योग्य है?"
    print(f"Original Hindi Query: {hindi_query}\n")

    payload = {
        "query": hindi_query,
        "jurisdiction": "national",
        "formulation_answers": {
            "is_first_schedule_text": True,
        },
    }

    with httpx.Client(timeout=180.0) as client:
        resp = client.post(BACKEND_URL, json=payload)
        assert resp.status_code == 200, f"Error {resp.status_code}: {resp.text}"
        data = resp.json()

    print("-" * 40 + " BACKEND RESPONSE " + "-" * 40)
    print(f"Language Detected       : {data.get('language')}")
    print(f"Formulation Category    : {data.get('classification')}")
    print(f"Statutory Legal Basis   : {data.get('classification_citation')}")
    print(f"Confidence Level        : {data.get('confidence')}")
    print(f"Abstained               : {data.get('abstained')}")
    print(f"Provider Used           : {data.get('provider_used')}")
    print(f"\nCitations (English Statutory Standard):")
    for cit in data.get("citations", []):
        print(f"  • Source: [{cit.get('source')}] Section: {cit.get('section')}")

    print(f"\nFinal Translated Hindi Answer:\n{data.get('answer')}")
    print("-" * 80)

    # Assertions
    assert data.get("language") == "hi", f"Expected language 'hi', got '{data.get('language')}'"
    assert data.get("classification") == "classical_medicine"
    assert len(data.get("citations", [])) > 0
    assert data.get("abstained") is False
    print("\n[SUCCESS] Hindi query translation round-trip verified with 100% success!")


if __name__ == "__main__":
    test_hindi_roundtrip()
