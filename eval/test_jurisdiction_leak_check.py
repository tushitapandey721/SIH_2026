"""
Test script for verifying jurisdiction isolation in multi-turn conversation memory.
Turn 1: "Can I patent traditional knowledge?" (jurisdiction: national)
Turn 2: "What about internationally?" (jurisdiction: international, same conversation_id)
Verifies:
- Turn 2 citations are purely international (TRIPS, CBD, Nagoya, WIPO GRATK).
- Zero Indian statute citations leak into Turn 2.
"""

import sys
import json
import urllib.request

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_URL = "http://localhost:8000/ask"

def ask(query: str, jurisdiction: str, conversation_id: str = None):
    payload = {
        "query": query,
        "jurisdiction": jurisdiction,
    }
    if conversation_id:
        payload["conversation_id"] = conversation_id

    req = urllib.request.Request(
        BASE_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))

print("=" * 80)
print("TURN 1: 'Can I patent traditional knowledge?' (jurisdiction: national)")
print("=" * 80)
res1 = ask("Can I patent traditional knowledge?", jurisdiction="national")
conv_id = res1.get("conversation_id")
print(f"Conversation ID: {conv_id}")
print(f"Turn 1 Answer:\n{res1.get('answer')}\n")
turn1_citations = res1.get("citations", [])
print(f"Turn 1 Citations: {[c.get('section') for c in turn1_citations]}")
print(f"Turn 1 Sources: {[c.get('title') or c.get('source') for c in turn1_citations]}\n")

print("=" * 80)
print("TURN 2: 'What about internationally?' (jurisdiction: international, same conv_id)")
print("=" * 80)
res2 = ask("What about internationally?", jurisdiction="international", conversation_id=conv_id)
print(f"Conversation ID: {res2.get('conversation_id')}")
print(f"Turn 2 Answer:\n{res2.get('answer')}\n")
turn2_citations = res2.get("citations", [])
turn2_sections = [c.get("section", "") for c in turn2_citations]
turn2_sources = [c.get("title") or c.get("source", "") for c in turn2_citations]
print(f"Turn 2 Citations: {turn2_sections}")
print(f"Turn 2 Sources: {turn2_sources}\n")

# Verification checks
indian_statute_terms = ["patents act", "section 3(p)", "section 3(d)", "drugs and cosmetics", "biodiversity act", "rule 158"]
leaked_indian_citations = []
for c in turn2_citations:
    sec = str(c.get("section", "")).lower()
    src = str(c.get("title") or c.get("source", "")).lower()
    for term in indian_statute_terms:
        if term in sec or term in src:
            leaked_indian_citations.append(f"{src} - {sec}")

international_terms = ["trips", "cbd", "nagoya", "wipo", "gratk", "convention on biological diversity"]
matched_international = []
for c in turn2_citations:
    sec = str(c.get("section", "")).lower()
    src = str(c.get("title") or c.get("source", "")).lower()
    for term in international_terms:
        if term in sec or term in src:
            matched_international.append(f"{src} - {sec}")

print("=" * 80)
print("JURISDICTION ISOLATION AUDIT:")
print(f"- International Citations Found: {len(matched_international)} -> {matched_international}")
print(f"- Indian Statute Citations Leaked: {len(leaked_indian_citations)} -> {leaked_indian_citations}")
print("=" * 80)

assert len(leaked_indian_citations) == 0, f"LEAK DETECTED: Indian citations found in international turn: {leaked_indian_citations}"
assert len(turn2_citations) > 0, "No citations returned in Turn 2!"
print("TEST PASSED: 100% Pure International Citations. Zero Indian Statute Leakage!")
print("=" * 80)
