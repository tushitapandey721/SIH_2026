"""Verification of source name normalization and near-duplicate resilience."""
import re
import requests

def canonical_source(s: str) -> str:
    cleaned = re.sub(r"[^\w\s]", "", str(s).lower())
    return " ".join(cleaned.split())

print("=== 1. UNIT TESTS FOR CANONICAL NORMALIZATION ===")
test_pairs = [
    ("Patents Act 1970", "Patents Act, 1970", True),
    ("WIPO GRATK Treaty (2024)", "WIPO GRATK Treaty 2024", True),
    ("The Biological Diversity Act, 2002", "the biological diversity act 2002", True),
    ("Nagoya Protocol", "nagoya   protocol", True),
    ("Patents Act, 1970", "WIPO GRATK Treaty", False),
]

for s1, s2, expected in test_pairs:
    c1 = canonical_source(s1)
    c2 = canonical_source(s2)
    matches = (c1 == c2)
    print(f"'{s1}' vs '{s2}' -> c1='{c1}', c2='{c2}' | Match={matches} (Expected={expected})")
    assert matches == expected

print(">>> ALL CANONICAL NORMALIZATION UNIT TESTS PASSED!")

print("\n=== 2. LIVE ENDPOINT TEST WITH CANONICAL NORMALIZATION ===")
res = requests.post(
    "http://127.0.0.1:8000/ask/compare",
    json={"query": "Can I patent traditional knowledge?"},
    timeout=30
)
assert res.status_code == 200
data = res.json()
print("Latency:", data.get("latency_ms"), "ms")
print("Zero Overlap:", data.get("is_zero_overlap"))
print("Shared Count:", data.get("shared_citations_count"))
print("Shared Sources:", data.get("shared_sources"))
assert data.get("is_zero_overlap") is True
assert data.get("shared_citations_count") == 0

print("\n>>> LIVE ENDPOINT TEST PASSED WITH CANONICAL NORMALIZATION ACTIVE!")
