"""Quick test script for TKDL helper."""
import json
from app.compliance.tkdl_helper import (
    detect_tkdl_trigger,
    extract_tkdl_hints,
    build_tkdl_pointer_payload,
)

test_queries = [
    ("My grandmother gave me a family recipe for a herbal joint pain oil made from classical Ayurvedic texts — can I patent it?", None, True),
    ("We want to formulate a new oil using sesame and ginger for arthritis.", "classical_medicine", True),
    ("Can I patent a software algorithm for inventory management?", None, False),
    ("What are the requirements for trademark registration in Class 5?", None, False),
    ("How do patent examiners use TKDL to check prior art for traditional formulations?", None, True),
    ("Is turmeric patentable under Section 3(p)?", None, True),
]

print("=== RUNNING TKDL TRIGGER TESTS ===")
for q, cls, expected in test_queries:
    result = detect_tkdl_trigger(q, cls)
    status = "PASS" if result == expected else "FAIL"
    print(f"[{status}] Query: {q[:50]}... | Cls: {cls} | Result: {result} (Expected: {expected})")
    assert result == expected, f"Trigger failed for '{q}'"

print("\n=== TESTING PAYLOAD GENERATION ===")
test_q = "My grandmother gave me a traditional recipe for a joint pain oil made with sesame and ginger from classical texts — can I patent it?"
payload = build_tkdl_pointer_payload(test_q)
print(json.dumps(payload, indent=2))

assert payload["triggered"] is True
assert payload["hints"]["formulation_category"].startswith("Taila Kalpana")
assert "Sandhivata" in payload["hints"]["therapeutic_area"]
assert any(ipc["code"] == "A61K 36/00" for ipc in payload["hints"]["ipc_classes"])
assert any(ipc["code"] == "A61P 19/02" for ipc in payload["hints"]["ipc_classes"])
assert "https://www.tkdl.res.in" == payload["official_portal_url"]
assert payload["hints"]["is_simulated_search"] is False
assert len(payload["patent_examiner_workflow"]) == 3
print("\nALL TKDL TESTS PASSED!")
