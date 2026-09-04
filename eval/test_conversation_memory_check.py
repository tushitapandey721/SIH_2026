"""
Test script for verifying multi-turn conversation memory using conversation_id.
Executes Step 1 and Step 2 of PROMPT 1:
1. Turn 1: "Is a classical Ayurvedic formulation patentable?" (jurisdiction: national)
2. Turn 2: "What about for a new drug instead?" with the SAME conversation_id, no history passed.
"""

import sys
import json
import urllib.request

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_URL = "http://localhost:8000/ask"

def ask(query: str, conversation_id: str = None):
    payload = {
        "query": query,
        "jurisdiction": "national",
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
print("STEP 1: Asking Turn 1: 'Is a classical Ayurvedic formulation patentable?'")
print("=" * 80)
res1 = ask("Is a classical Ayurvedic formulation patentable?")
conv_id = res1.get("conversation_id")
print(f"Conversation ID returned: {conv_id}")
print(f"Turn 1 Answer:\n{res1.get('answer')}\n")
print(f"Turn 1 Citations: {[c.get('section') for c in res1.get('citations', [])]}\n")

print("=" * 80)
print("STEP 2: Asking Turn 2 with SAME conversation_id: 'What about for a new drug instead?'")
print("=" * 80)
res2 = ask("What about for a new drug instead?", conversation_id=conv_id)
print(f"Conversation ID used: {res2.get('conversation_id')}")
print(f"Turn 2 Answer:\n{res2.get('answer')}\n")
print(f"Turn 2 Citations: {[c.get('section') for c in res2.get('citations', [])]}\n")
print(f"Turn 2 Classification: {res2.get('classification')}")
print("=" * 80)
