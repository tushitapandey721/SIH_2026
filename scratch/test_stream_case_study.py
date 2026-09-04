# -*- coding: utf-8 -*-
import requests
import json

BASE_URL = "http://localhost:8000"

def test_stream(query, expect_triggered):
    r = requests.post(
        f"{BASE_URL}/ask/stream",
        json={"query": query, "jurisdiction": "national"},
        stream=True
    )
    assert r.status_code == 200
    has_case_study = False
    for line in r.iter_lines(decode_unicode=True):
        if line and line.startswith("data: "):
            try:
                event = json.loads(line[6:])
                if event.get("stage") == "tkdl_pointer":
                    if event.get("data", {}).get("case_study", {}).get("triggered"):
                        has_case_study = True
                if event.get("stage") == "complete":
                    data = event.get("data", {})
                    if data.get("case_study", {}).get("triggered") or data.get("tkdl_pointer", {}).get("case_study", {}).get("triggered"):
                        has_case_study = True
            except Exception:
                pass
    assert has_case_study == expect_triggered, f"Failed for query '{query}': expected {expect_triggered}, got {has_case_study}"
    print(f"[PASS] Stream test for '{query[:45]}...' -> Case Study Triggered: {has_case_study} (Expected: {expect_triggered})")

if __name__ == "__main__":
    test_stream("Can someone else patent my grandmother's classical Ayurvedic formulation?", True)
    test_stream("What are the labelling requirements under Rule 161?", False)
    test_stream("How do I register a trademark?", False)
    print("ALL STREAM CASE STUDY TESTS PASSED!")
