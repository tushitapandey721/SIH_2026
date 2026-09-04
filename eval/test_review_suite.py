"""Comprehensive review and verification suite for:
1. Query validation (empty, whitespace, missing field) -> 400 Bad Request
2. SSE Real-time Stage Streaming
3. Groq -> Mistral fallback verification (and restoration)
4. Corpus Provenance dynamic manifest loading (17 sources)
"""

import sys
import os
import json
import httpx

# Ensure UTF-8 output on Windows
if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

BACKEND_URL = "http://127.0.0.1:8000"


def test_1_query_validation():
    print("=" * 80)
    print("ITEM 1: QUERY VALIDATION (400 BAD REQUEST TESTS)")
    print("=" * 80)

    client = httpx.Client(base_url=BACKEND_URL, timeout=30.0)

    # Test A: Empty string
    resp_empty = client.post("/ask", json={"query": "", "jurisdiction": "national"})
    print(f"[Test A: Empty string ''] Status: {resp_empty.status_code}, Detail: {resp_empty.json()}")
    assert resp_empty.status_code == 400, f"Expected 400, got {resp_empty.status_code}"
    assert "empty or whitespace" in resp_empty.json().get("detail", "").lower()

    # Test B: Whitespace-only
    resp_ws = client.post("/ask", json={"query": "   \n\t  ", "jurisdiction": "national"})
    print(f"[Test B: Whitespace-only] Status: {resp_ws.status_code}, Detail: {resp_ws.json()}")
    assert resp_ws.status_code == 400, f"Expected 400, got {resp_ws.status_code}"
    assert "empty or whitespace" in resp_ws.json().get("detail", "").lower()

    # Test C: Missing query field
    resp_missing = client.post("/ask", json={"jurisdiction": "national"})
    print(f"[Test C: Missing query field] Status: {resp_missing.status_code}, Detail: {resp_missing.json()}")
    assert resp_missing.status_code == 400, f"Expected 400, got {resp_missing.status_code}"
    assert "query" in resp_missing.json().get("detail", "").lower()

    # Test D: Empty query on /ask/stream
    resp_stream_empty = client.post("/ask/stream", json={"query": ""})
    print(f"[Test D: /ask/stream Empty query] Status: {resp_stream_empty.status_code}, Detail: {resp_stream_empty.json()}")
    assert resp_stream_empty.status_code == 400

    print("\n[SUCCESS] ITEM 1 PASSED: All invalid/missing queries return clean 400 Bad Request errors!")


def test_2_sse_stage_streaming():
    print("\n" + "=" * 80)
    print("ITEM 2: REAL-TIME STAGE PROGRESS STREAMING (/ask/stream)")
    print("=" * 80)

    payload = {
        "query": "Is a classical Ayurvedic formulation patentable?",
        "jurisdiction": "national",
        "formulation_answers": {"is_first_schedule_text": True},
    }

    stages_received = []
    with httpx.Client(base_url=BACKEND_URL, timeout=120.0) as client:
        with client.stream("POST", "/ask/stream", json=payload) as resp:
            assert resp.status_code == 200
            for line in resp.iter_lines():
                if line.startswith("data: "):
                    event = json.loads(line[6:])
                    stage = event.get("stage")
                    msg = event.get("message") or (f"Completed with {len(event.get('data', {}).get('citations', []))} citations" if stage == "complete" else "")
                    stages_received.append(stage)
                    print(f"  -> [SSE Stage Event] {stage:20s} | {msg}")

    assert "detect_language" in stages_received
    assert "retrieval" in stages_received
    assert "synthesis" in stages_received
    assert "complete" in stages_received
    print("\n[SUCCESS] ITEM 2 PASSED: Backend SSE stream broadcasts genuine pipeline execution stages in real-time!")


def test_3_groq_mistral_fallback():
    print("\n" + "=" * 80)
    print("ITEM 3: GROQ -> MISTRAL FALLBACK & RESTORATION VERIFICATION")
    print("=" * 80)

    from app.llm.client import get_completion
    from app.llm.prompts import SYSTEM_PROMPT

    original_groq_key = os.environ.get("GROQ_API_KEY", "")

    test_system = "You are a legal assistant. Respond ONLY in valid JSON matching: {\"answer\": str, \"citations\": [], \"confidence\": \"high\", \"abstained\": false}"
    test_user = "State briefly that Section 3(p) of the Patents Act 1970 excludes traditional knowledge."

    # Part A: Force Groq failure by setting invalid key
    print("\n[Part A: Simulating Groq Failure with invalid API key]")
    os.environ["GROQ_API_KEY"] = "gsk_invalid_simulated_key_12345"

    fallback_res = get_completion(
        system_prompt=test_system,
        user_prompt=test_user,
        max_tokens=256,
    )
    print(f"  Provider Used : {fallback_res.get('provider_used')}")
    print(f"  Response Text : {fallback_res.get('text')[:180]}...")
    assert fallback_res.get("provider_used") == "mistral", f"Expected 'mistral', got {fallback_res.get('provider_used')}"

    # Part B: Restore real Groq key
    print("\n[Part B: Restoring genuine Groq key]")
    os.environ["GROQ_API_KEY"] = original_groq_key

    normal_res = get_completion(
        system_prompt=test_system,
        user_prompt=test_user,
        max_tokens=256,
    )
    print(f"  Provider Used : {normal_res.get('provider_used')}")
    print(f"  Response Text : {normal_res.get('text')[:180]}...")
    assert normal_res.get("provider_used") == "groq", f"Expected 'groq', got {normal_res.get('provider_used')}"

    print("\n[SUCCESS] ITEM 3 PASSED: Groq -> Mistral fallback verified and normal Groq operation restored!")


def test_4_corpus_provenance():
    print("\n" + "=" * 80)
    print("ITEM 4: DYNAMIC CORPUS PROVENANCE (GET /corpus)")
    print("=" * 80)

    client = httpx.Client(base_url=BACKEND_URL, timeout=10.0)
    resp = client.get("/corpus")
    assert resp.status_code == 200, f"Error {resp.status_code}: {resp.text}"

    data = resp.json()
    total = data.get("total_documents")
    nat_count = data.get("national_count")
    intl_count = data.get("international_count")

    print(f"Total Sources Indexed        : {total}")
    print(f"National Jurisdiction Sources : {nat_count}")
    print(f"International Treaties Sources: {intl_count}")

    print("\n[National Statutes Samples]:")
    for doc in data.get("national", [])[:4]:
        print(f"  • [{doc['id']}] {doc['title']} ({doc['authority']}, {doc['year']}) - Prefix: {doc['citation_prefix']}")

    print("\n[International Treaties Samples]:")
    for doc in data.get("international", [])[:3]:
        print(f"  • [{doc['id']}] {doc['title']} ({doc['authority']}, {doc['year']}) - Prefix: {doc['citation_prefix']}")

    assert total == 17, f"Expected 17 documents in manifest, found {total}"
    assert nat_count == 12
    assert intl_count == 5
    print("\n[SUCCESS] ITEM 4 PASSED: Dynamic corpus provenance returns all 17 sources grouped by jurisdiction!")


if __name__ == "__main__":
    test_1_query_validation()
    test_2_sse_stage_streaming()
    test_3_groq_mistral_fallback()
    test_4_corpus_provenance()
    print("\n" + "=" * 80)
    print("ALL 4 REVIEW TEST SUITES PASSED WITH 100% SUCCESS!")
    print("=" * 80)
