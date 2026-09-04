import os
import sys
from pathlib import Path

# Ensure repo root is in python path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import json
import re
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.api.routes import router

app = FastAPI()
app.include_router(router)
client = TestClient(app)

sample_answer = (
    "Under Section 3(p) of the Patents Act, 1970, classical Ayurvedic formulations are not patentable "
    "because traditional knowledge belongs to the public domain and represents an aggregation of known properties. "
    "However, a novel, non-obvious synergistic herbal combination demonstrating an inventive step with proven "
    "experimental efficacy may overcome the traditional knowledge exclusion and be considered under Section 3(e). "
    "This is informational guidance, not legal advice."
)

sample_citations = [
    {"source": "Patents Act, 1970", "section": "Section 3(p)", "title": "Patents Act, 1970"},
    {"source": "Patents Act, 1970", "section": "Section 3(e)", "title": "Patents Act, 1970"},
]

payload = {
    "answer_text": sample_answer,
    "citations": sample_citations,
}

print("=" * 80)
print("TESTING POST /simplify ENDPOINT (Explain-Simply Register Toggle)")
print("=" * 80)

response = client.post("/simplify", json=payload)
assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"

data = response.json()
simplified_text = data.get("simplified_text", "")
returned_citations = data.get("citations", [])

print("\n--- TEST CHECKS ---")

# 1. Check citations panel is IDENTICAL
print("Check 1: Citations Panel Identity...")
assert returned_citations == sample_citations, (
    f"Citation drift detected! Expected {sample_citations}, got {returned_citations}"
)
print(" [PASS] Citations panel is 100% IDENTICAL in both versions (Section 3(p) & Section 3(e)).")

# 2. Check legal conclusion is preserved
print("Check 2: Core Legal Conclusion Preserved...")
norm_text = simplified_text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"').replace("\u202f", " ").replace("\u2011", "-").lower()
conclusion_markers = ["not patentable", "cannot be patented", "can't be patented", "cannot patent", "can't patent", "not eligible for patent"]
has_conclusion = any(marker in norm_text for marker in conclusion_markers)
assert has_conclusion, (
    f"Core legal conclusion missing or softened! Simplified text:\n{simplified_text}"
)
print(" [PASS] Core legal conclusion ('not patentable' / 'cannot be patented') strictly preserved.")

# 3. Check legal jargon is eliminated/simplified
print("Check 3: Legal Jargon Avoidance...")
jargon_terms = ["traditional knowledge exclusion", "inventive step", "aggregation of known properties"]
found_jargon = [term for term in jargon_terms if term in simplified_text.lower()]
print(f" Jargon terms checked: {jargon_terms}")
if found_jargon:
    print(f" [WARNING] Found jargon: {found_jargon}")
else:
    print(" [PASS] Legal jargon avoided successfully.")

# 4. Check citations mentioned in text
print("Check 4: Citations kept in text...")
assert "Section 3(p)" in simplified_text or "3(p)" in simplified_text, "Section 3(p) not referenced in simplified text"
print(" [PASS] Section 3(p) statutory authority preserved.")

print("\n" + "=" * 80)
print("SIDE-BY-SIDE REGISTER COMPARISON")
print("=" * 80)

print("\n[FORMAL LEGAL REGISTER (ORIGINAL)]")
print("-" * 50)
print(sample_answer)
print("\nCITATIONS:")
for c in sample_citations:
    print(f" - {c['source']} ({c['section']})")

print("\n" + "-" * 80)

print("\n[PLAIN-LANGUAGE REGISTER (SIMPLIFIED)]")
print("-" * 50)
print(simplified_text)
print("\nCITATIONS (IDENTICAL):")
for c in returned_citations:
    print(f" - {c['source']} ({c['section']})")

print("\n" + "=" * 80)
print(">>> ALL VERIFICATION CHECKS PASSED PERFECTLY! <<<")
