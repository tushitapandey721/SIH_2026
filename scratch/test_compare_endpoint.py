"""Unit and integration test for POST /ask/compare side-by-side comparison endpoint."""
import time
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

print("=================================================================")
print("TEST 1: Symmetrical Substantive Query — 'Can I patent traditional knowledge?'")
print("=================================================================")

t0 = time.perf_counter()
payload_sym = {
    "query": "Can I patent traditional knowledge?",
    "formulation_answers": {},
    "history": [],
}
res_sym = requests.post(f"{BASE_URL}/ask/compare", json=payload_sym, timeout=40)
lat_wall_ms = (time.perf_counter() - t0) * 1000

print(f"HTTP Status: {res_sym.status_code}")
assert res_sym.status_code == 200, f"Expected 200, got {res_sym.status_code}: {res_sym.text}"
data_sym = res_sym.json()

nat = data_sym.get("national", {})
intl = data_sym.get("international", {})

print(f"Backend Reported Latency: {data_sym.get('latency_ms')} ms")
print(f"Wall Clock Request Latency: {lat_wall_ms:.1f} ms")
print(f"Is Zero Overlap: {data_sym.get('is_zero_overlap')}")
print(f"Shared Citations Count: {data_sym.get('shared_citations_count')}")
print(f"Shared Sources: {data_sym.get('shared_sources')}")

print("\n--- NATIONAL (India) ---")
print("Abstained:", nat.get("abstained"))
print("Confidence:", nat.get("confidence"))
print("Answer Preview:", nat.get("answer", "")[:200].replace("\n", " ").encode("ascii", "ignore").decode(), "...")
print("Citations Count:", len(nat.get("citations", [])))
for c in nat.get("citations", []):
    print(f"  * {c.get('source')} | Sec {c.get('section')}".encode("ascii", "ignore").decode())

print("\n--- INTERNATIONAL (Treaties) ---")
print("Abstained:", intl.get("abstained"))
print("Confidence:", intl.get("confidence"))
print("Answer Preview:", intl.get("answer", "")[:200].replace("\n", " ").encode("ascii", "ignore").decode(), "...")
print("Citations Count:", len(intl.get("citations", [])))
for c in intl.get("citations", []):
    print(f"  * {c.get('source')} | Art/Sec {c.get('section')}".encode("ascii", "ignore").decode())

assert nat.get("abstained") is False, "National answer should not abstain for traditional knowledge patentability!"
assert intl.get("abstained") is False, "International answer should not abstain for traditional knowledge patentability!"
assert data_sym.get("is_zero_overlap") is True, "Expected zero shared citation sources between National and International!"
assert data_sym.get("shared_citations_count") == 0

# Verify specific statutory grounding
nat_text = json.dumps(nat).lower()
intl_text = json.dumps(intl).lower()

assert "section 3(p)" in nat_text or "patents act" in nat_text, "National should cite Patents Act / Section 3(p)"
assert "wipo" in intl_text or "nagoya" in intl_text or "gratk" in intl_text or "cbd" in intl_text, "International should cite WIPO GRATK / Nagoya / CBD"

print("\n>>> TEST 1 PASSED! (Both substantive, zero overlap confirmed)")

print("\n=================================================================")
print("TEST 2: Asymmetric Query — 'What are the labeling requirements under Rule 161 of the Drugs and Cosmetics Rules?'")
print("=================================================================")

payload_asym = {
    "query": "What are the labeling requirements under Rule 161 of the Drugs and Cosmetics Rules?",
    "formulation_answers": {},
    "history": [],
}
t0 = time.perf_counter()
res_asym = requests.post(f"{BASE_URL}/ask/compare", json=payload_asym, timeout=40)
lat_asym_ms = (time.perf_counter() - t0) * 1000

assert res_asym.status_code == 200
data_asym = res_asym.json()
nat_asym = data_asym.get("national", {})
intl_asym = data_asym.get("international", {})

print(f"Backend Reported Latency: {data_asym.get('latency_ms')} ms")
print(f"Wall Clock Latency: {lat_asym_ms:.1f} ms")
print(f"National Abstained: {nat_asym.get('abstained')}")
print(f"National Citations: {len(nat_asym.get('citations', []))}")
print(f"International Abstained: {intl_asym.get('abstained')}")
print(f"International Citations: {len(intl_asym.get('citations', []))}")
print(f"Zero Overlap: {data_asym.get('is_zero_overlap')}")

assert nat_asym.get("abstained") is False, "National should answer Rule 161 labeling requirements!"
assert intl_asym.get("abstained") is True, "International should abstain for specific Indian Rule 161 labeling!"
assert data_asym.get("is_zero_overlap") is True

print("\n>>> TEST 2 PASSED! (Asymmetric handling verified: National answered, International gracefully abstained)")
print("\n=================================================================")
print("ALL BACKEND COMPARISON ENDPOINT TESTS PASSED SUCCESSFULLY!")
print("=================================================================")
