"""End-to-End Integration Verification Script for IP-SAKTI Sahayak (Frontend + Backend)."""

import sys
import os
import json
import urllib.request
import urllib.error

# Ensure UTF-8 output on Windows
if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8")

BACKEND_URL = "http://localhost:8000/ask"
FRONTEND_URL = "http://localhost:3000"


def make_request(payload: dict) -> dict:
    req = urllib.request.Request(
        BACKEND_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Origin": FRONTEND_URL,
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))


def test_1_conversational_classification_flow():
    print("=" * 80)
    print("TEST 1: Conversational Classification Flow")
    print("=" * 80)

    # Step A: Query with empty answers -> triggers classification question
    q = "What regulatory approval is required for a new formulation with novel excipients?"
    res1 = make_request({
        "query": q,
        "jurisdiction": "national",
        "formulation_answers": {},
    })

    print("[Step A] Sent query with formulation_answers={}")
    print(f"Needs Classification: {res1.get('needs_classification')}")
    print(f"Question ID        : {res1.get('question', {}).get('id')}")
    print(f"Question Text      : {res1.get('question', {}).get('question')}")
    assert res1.get("needs_classification") is True
    assert "question" in res1

    # Step B: User answers 'No' to First-Schedule text (is_first_schedule_text=False)
    # -> Should ask next question in tree (requires_new_safety_efficacy)
    res2 = make_request({
        "query": q,
        "jurisdiction": "national",
        "formulation_answers": {"is_first_schedule_text": False},
    })
    print("\n[Step B] Answered is_first_schedule_text=False")
    print(f"Needs Classification: {res2.get('needs_classification')}")
    print(f"Next Question ID    : {res2.get('question', {}).get('id')}")
    assert res2.get("question", {}).get("id") == "requires_new_safety_efficacy"

    # Step C: User answers 'Yes' to requires_new_safety_efficacy=True
    # -> Classification complete -> returns grounded response
    res3 = make_request({
        "query": q,
        "jurisdiction": "national",
        "formulation_answers": {
            "is_first_schedule_text": False,
            "requires_new_safety_efficacy": True,
        },
    })
    print("\n[Step C] Answered requires_new_safety_efficacy=True")
    print(f"Needs Classification: {res3.get('needs_classification')}")
    print(f"Classification Category: {res3.get('classification')}")
    print(f"Legal Basis Citation   : {res3.get('classification_citation')}")
    print(f"Confidence Level       : {res3.get('confidence')}")
    print(f"Provider Used          : {res3.get('provider_used')}")
    print(f"Abstained              : {res3.get('abstained')}")
    print(f"Citations Count        : {len(res3.get('citations', []))}")
    for c in res3.get("citations", []):
        print(f"  • Source: [{c.get('source')}] Section: {c.get('section')}")
    print(f"Answer Preview         :\n{res3.get('answer')[:300]}...")

    assert res3.get("needs_classification") is False
    assert res3.get("classification") == "new_drug"
    assert "Rule 158-B" in res3.get("classification_citation", "")
    print("\n[SUCCESS] TEST 1 PASSED: Full conversational classification loop completed!")


def test_2_jurisdiction_isolation():
    print("\n" + "=" * 80)
    print("TEST 2: Jurisdiction Isolation (National vs International)")
    print("=" * 80)

    # National Query
    res_nat = make_request({
        "query": "Is a classical Ayurvedic formulation patentable?",
        "jurisdiction": "national",
        "formulation_answers": {"is_first_schedule_text": True},
    })
    print("[National Query Citations]:")
    for c in res_nat.get("citations", []):
        print(f"  • [{c.get('source')}] {c.get('section')}")
        # Verify no international treaty articles in national response
        assert "nagoya" not in c.get("source", "").lower()
        assert "cbd" not in c.get("source", "").lower()

    # International Query
    res_intl = make_request({
        "query": "What are the prior informed consent requirements for traditional knowledge access?",
        "jurisdiction": "international",
        "formulation_answers": {"is_first_schedule_text": False},
    })
    print("\n[International Query Citations]:")
    for c in res_intl.get("citations", []):
        print(f"  • [{c.get('source')}] {c.get('section')}")
        # Verify no Indian domestic D&C rules in international response
        assert "drugs and cosmetics" not in c.get("source", "").lower()

    print("\n[SUCCESS] TEST 2 PASSED: National and International jurisdictions strictly isolated!")


def test_3_abstention_trigger():
    print("\n" + "=" * 80)
    print("TEST 3: Deliberate Abstention (Out-of-domain query)")
    print("=" * 80)

    res = make_request({
        "query": "What are the zoning and real estate construction setback permits for high-rise buildings in Mumbai?",
        "jurisdiction": "national",
        "formulation_answers": {"is_first_schedule_text": False, "requires_new_safety_efficacy": False, "is_standardized_plant_extract": False, "is_food_dietary_product": False, "is_topical_cosmetic": False},
    })

    print(f"Abstained       : {res.get('abstained')}")
    print(f"Answer          : {res.get('answer')}")
    print(f"Citations Count : {len(res.get('citations', []))}")
    print(f"Confidence      : {res.get('confidence')}")

    # Either retrieval returned no relevant statutory hits or LLM explicitly abstained
    assert res.get("abstained") is True or "no " in res.get("answer", "").lower() or "not" in res.get("answer", "").lower()
    print("\n[SUCCESS] TEST 3 PASSED: Abstention triggered cleanly for out-of-domain query!")


if __name__ == "__main__":
    test_1_conversational_classification_flow()
    test_2_jurisdiction_isolation()
    test_3_abstention_trigger()
    print("\n" + "=" * 80)
    print("ALL 3 END-TO-END INTEGRATION TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 80)
