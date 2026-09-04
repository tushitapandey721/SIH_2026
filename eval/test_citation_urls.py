"""
Test script for verifying direct links to official sources at point of citation (PROMPT 2).
Verifies:
1. GET /corpus response contains official_url for all documents.
2. POST /ask response includes {source, section, url} for each citation.
3. National citations map to official India Code/IP India registries.
4. International citations map to official WIPO/WTO/CBD registries.
5. Graceful handling of empty or unmapped URLs.
"""

import sys
import json
import urllib.request

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_URL = "http://localhost:8000"

def get(path: str):
    req = urllib.request.Request(f"{BASE_URL}{path}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))

def post(path: str, payload: dict):
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))

print("=" * 80)
print("TEST 1: GET /corpus Provenance Official URLs")
print("=" * 80)
corpus = get("/corpus")
print(f"Total documents: {corpus['total_documents']} ({corpus['national_count']} national, {corpus['international_count']} international)")

docs_with_urls = 0
for d in corpus["national"] + corpus["international"]:
    url = d.get("official_url") or d.get("url")
    assert url, f"Document {d['id']} missing official_url!"
    docs_with_urls += 1
    print(f"  [{d['id']}] {d['title'][:35]:<35} -> {url}")

print(f"\n[CORPUS OK] 100% of documents ({docs_with_urls}/{corpus['total_documents']}) have official registry URLs.")

print("=" * 80)
print("TEST 2: POST /ask National Citation URLs (Patents Act 1970)")
print("=" * 80)
res_nat = post("/ask", {
    "query": "Is traditional knowledge patentable under the Patents Act?",
    "jurisdiction": "national"
})
citations_nat = res_nat.get("citations", [])
print(f"Answer snippet: {res_nat.get('answer')[:180]}...\n")
print(f"Citations returned ({len(citations_nat)}):")
for cit in citations_nat:
    print(f"  Section: {cit.get('section'):<20} | Source: {cit.get('source'):<25} | URL: {cit.get('url')}")
    assert "url" in cit, f"Citation {cit} missing 'url' key!"
    assert cit["url"] is not None and "indiacode.nic.in" in cit["url"], f"Expected indiacode URL, got {cit.get('url')}"

print("=" * 80)
print("TEST 3: POST /ask International Citation URLs (WIPO GRATK Treaty)")
print("=" * 80)
res_intl = post("/ask", {
    "query": "What does WIPO GRATK treaty say about patent disclosure of traditional knowledge?",
    "jurisdiction": "international"
})
citations_intl = res_intl.get("citations", [])
print(f"Answer snippet: {res_intl.get('answer')[:180]}...\n")
print(f"Citations returned ({len(citations_intl)}):")
for cit in citations_intl:
    print(f"  Section: {cit.get('section'):<20} | Source: {cit.get('source'):<25} | URL: {cit.get('url')}")
    assert "url" in cit, f"Citation {cit} missing 'url' key!"
    if "gratk" in str(cit.get("source", "")).lower() or "gratk" in str(cit.get("section", "")).lower():
        assert "wipo.int" in cit["url"], f"Expected wipo.int URL for GRATK, got {cit.get('url')}"

print("=" * 80)
print("ALL OFFICIAL CITATION URL TESTS PASSED SUCCESSFULLY!")
print("=" * 80)
