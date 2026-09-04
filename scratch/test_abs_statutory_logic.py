"""Test script to thoroughly verify ABS compliance decision logic, trigger detection, and all 5 outcomes."""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.compliance.abs_helper import (
    detect_abs_trigger,
    extract_abs_initial_answers,
    evaluate_abs_compliance,
    get_next_abs_question,
    process_abs_decision_flow,
)

def run_tests():
    print("=== 1. TRIGGER DETECTION TESTS ===")
    test_query = "I want to export a herbal supplement made from a plant sourced in Kerala — what approval do I need?"
    assert detect_abs_trigger(test_query) is True, f"Failed on test query: {test_query}"
    print("[PASS] Test prompt triggered successfully.")

    positives = [
        "What are the ABS obligations for commercializing ashwagandha from Madhya Pradesh?",
        "Do foreign companies need NBA approval to access marine algae from Tamil Nadu?",
        "I want to sell a cosmetic cream made with neem leaf extract sourced from Karnataka",
        "State Biodiversity Board intimation rules under the BD Act",
        "Exporting traditional herbal medicine to Europe from Himalayas",
    ]
    for p in positives:
        assert detect_abs_trigger(p) is True, f"Positive query failed: {p}"
    print(f"[PASS] All {len(positives)} positive trigger queries succeeded.")

    negatives = [
        "What is Section 3(p) of the Patents Act?",
        "Difference between trademark and copyright in India",
        "Can a software algorithm be patented in India?",
        "Who is the Controller General of Patents?",
    ]
    for n in negatives:
        assert detect_abs_trigger(n) is False, f"Negative query falsely triggered: {n}"
    print(f"[PASS] All {len(negatives)} negative trigger queries correctly rejected.")

    print("\n=== 2. INITIAL ANSWER EXTRACTION TESTS ===")
    extracted = extract_abs_initial_answers(test_query)
    print("Extracted from test prompt:", extracted)
    assert extracted.get("is_sourced_from_india") is True, "Should detect sourced from India (Kerala)"
    assert extracted.get("is_commercial_use") is True, "Should detect commercial use (export herbal supplement)"
    assert "is_foreign_entity" not in extracted, "Entity type should be pending"
    print("[PASS] Extraction from test prompt correct.")

    print("\n=== 3. STATUTORY DECISION TABLE TESTS (ALL 5 OUTCOMES) ===")

    # Outcome 1: Sourced outside India
    o1 = evaluate_abs_compliance({"is_sourced_from_india": False})
    assert o1["requires_nba_approval"] is False
    assert o1["requires_sbb_intimation"] is False
    assert "Section 3(1)" in o1["applicable_provision"] and "Section 7(1)" in o1["applicable_provision"]
    print("[PASS] Outcome 1: Outside India -> NBA=False, SBB=False.")

    # Outcome 2: Indian Domestic Entity + Commercial Use (Kerala test query)
    o2 = evaluate_abs_compliance(
        {"is_sourced_from_india": True, "is_commercial_use": True, "is_foreign_entity": False},
        query=test_query,
    )
    assert o2["requires_nba_approval"] is False
    assert o2["requires_sbb_intimation"] is True
    assert "Section 7(1)" in o2["applicable_provision"]
    assert "Kerala State Biodiversity Board" in o2["relevant_forms"][0]
    assert o2["sbb_state"] == "Kerala"
    print("[PASS] Outcome 2: Domestic + Commercial Export -> NBA=False, SBB=True (Kerala KSBB), Section 7(1).")

    # Outcome 3: Foreign Entity + Commercial Use (Kerala test query)
    o3 = evaluate_abs_compliance(
        {"is_sourced_from_india": True, "is_commercial_use": True, "is_foreign_entity": True},
        query=test_query,
    )
    assert o3["requires_nba_approval"] is True
    assert o3["requires_sbb_intimation"] is False
    assert "Section 3(1)" in o3["applicable_provision"]
    assert "Form 2" in o3["relevant_forms"][0]
    print("[PASS] Outcome 3: Foreign Entity + Commercial Export -> NBA=True, SBB=False, Section 3(1), Form 2.")

    # Outcome 4: Indian Domestic Entity + Research Only
    o4 = evaluate_abs_compliance(
        {"is_sourced_from_india": True, "is_commercial_use": False, "is_foreign_entity": False}
    )
    assert o4["requires_nba_approval"] is False
    assert o4["requires_sbb_intimation"] is False
    assert "Section 7(1)" in o4["applicable_provision"]
    print("[PASS] Outcome 4: Domestic + Research -> NBA=False, SBB=False, Section 7(1).")

    # Outcome 5: Foreign Entity + Research Only
    o5 = evaluate_abs_compliance(
        {"is_sourced_from_india": True, "is_commercial_use": False, "is_foreign_entity": True}
    )
    assert o5["requires_nba_approval"] is True
    assert o5["requires_sbb_intimation"] is False
    assert "Section 3(1)" in o5["applicable_provision"]
    assert "Form 1" in o5["relevant_forms"][0]
    print("[PASS] Outcome 5: Foreign Entity + Research -> NBA=True, SBB=False, Section 3(1), Form 1.")

    print("\n=== 4. PROCESS DECISION FLOW (TEST QUERY FLOW) ===")
    flow1 = process_abs_decision_flow(test_query)
    assert flow1["triggered"] is True
    assert flow1["status"] == "needs_input"
    assert flow1["next_question"]["id"] == "is_foreign_entity"
    print(f"[PASS] Flow asked pending question: '{flow1['next_question']['question']}'")

    # User answers that they are a domestic Indian entity
    flow2 = process_abs_decision_flow(test_query, user_answers={"is_foreign_entity": False})
    assert flow2["status"] == "completed"
    assert flow2["result"]["requires_sbb_intimation"] is True
    assert flow2["result"]["requires_nba_approval"] is False
    print("[PASS] Flow resolved completely with user answer: SBB Intimation required (Kerala KSBB).")

    print("\nALL TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_tests()
