"""Test script verifying gated formulation classification:
1. General statutory query ("What does Section 3(p) of the Patents Act prohibit?") -> Direct answer (NO classification prompt)
2. Specific product formulation query ("I want to sell my grandmother's Ayurvedic oil recipe, what IP protection do I need?") -> Triggers classification prompt!
"""

import sys
import os
import json
import httpx

# Ensure UTF-8 output on Windows
if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8")

BACKEND_URL = "http://127.0.0.1:8000"


def test_gated_classification():
    client = httpx.Client(base_url=BACKEND_URL, timeout=120.0)

    # -------------------------------------------------------------------------
    # TEST 1: Direct Statutory Question (MUST NOT trigger classification)
    # -------------------------------------------------------------------------
    print("=" * 80)
    print("TEST 1: Direct Statutory Question -> Should Answer Directly (No Classification)")
    print("=" * 80)
    query_1 = "What does Section 3(p) of the Patents Act prohibit?"
    print(f"Inquiry: {query_1}")

    resp_1 = client.post("/ask", json={"query": query_1, "jurisdiction": "national", "formulation_answers": {}})
    assert resp_1.status_code == 200, f"Error {resp_1.status_code}: {resp_1.text}"
    data_1 = resp_1.json()

    print(f"\nResponse Metadata:")
    print(f"  Needs Classification : {data_1.get('needs_classification')}")
    print(f"  Classification Basis : {data_1.get('classification_citation')}")
    print(f"  Confidence Level     : {data_1.get('confidence')}")
    print(f"  Abstained            : {data_1.get('abstained')}")
    print(f"  Citations Count      : {len(data_1.get('citations', []))}")
    for c in data_1.get("citations", []):
        print(f"    • [{c.get('source')}] {c.get('section')}")
    print(f"\nAnswer Preview:\n{data_1.get('answer')[:260]}...\n")

    assert data_1.get("needs_classification") is False, "FAILED: General statutory question triggered classification!"
    assert len(data_1.get("citations", [])) > 0, "FAILED: Expected direct statutory citations!"
    print("[SUCCESS] TEST 1 PASSED: General statutory question answered directly without classification prompt!")

    # -------------------------------------------------------------------------
    # TEST 2: Product-Specific Formulation Query (MUST trigger classification)
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("TEST 2: Product Formulation Query -> MUST Trigger Classification Prompt")
    print("=" * 80)
    query_2 = "I want to sell my grandmother's Ayurvedic oil recipe, what IP protection do I need?"
    print(f"Inquiry: {query_2}")

    resp_2 = client.post("/ask", json={"query": query_2, "jurisdiction": "national", "formulation_answers": {}})
    assert resp_2.status_code == 200, f"Error {resp_2.status_code}: {resp_2.text}"
    data_2 = resp_2.json()

    print(f"\nInitial Response Metadata:")
    print(f"  Needs Classification : {data_2.get('needs_classification')}")
    print(f"  Question ID          : {data_2.get('question', {}).get('id')}")
    print(f"  Question Text        : {data_2.get('question', {}).get('question')}")

    assert data_2.get("needs_classification") is True, "FAILED: Product-specific query failed to trigger classification!"
    assert "question" in data_2

    # Step 2: Answer the classification question
    resp_2_answered = client.post(
        "/ask",
        json={
            "query": query_2,
            "jurisdiction": "national",
            "formulation_answers": {"is_first_schedule_text": True},
        },
    )
    assert resp_2_answered.status_code == 200
    data_2_final = resp_2_answered.json()

    print(f"\nFinal Response after Classification:")
    print(f"  Needs Classification : {data_2_final.get('needs_classification')}")
    print(f"  Classified Category  : {data_2_final.get('classification')}")
    print(f"  Legal Basis Citation : {data_2_final.get('classification_citation')}")
    print(f"  Citations Count      : {len(data_2_final.get('citations', []))}")
    print(f"\nAnswer Preview:\n{data_2_final.get('answer')[:260]}...\n")

    assert data_2_final.get("needs_classification") is False
    assert data_2_final.get("classification") == "classical_medicine"
    print("[SUCCESS] TEST 2 PASSED: Product formulation query properly triggered and completed classification!")


if __name__ == "__main__":
    test_gated_classification()
    print("\n" + "=" * 80)
    print("BOTH TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 80)
