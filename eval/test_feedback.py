"""Test suite for Prompt 3: Answer feedback mechanism (thumbs up/down).

Validates:
1. POST /feedback with rating 'up' succeeds and logs entry.
2. POST /feedback with rating 'down' and optional comment succeeds and logs entry.
3. POST /feedback validates required rating field and enum values.
4. Feedback entries are accurately appended to /data/feedback_log.csv.
5. GET /feedback returns stored feedback records.
"""

import os
import csv
import json
import urllib.request
import urllib.error
from pathlib import Path

BASE_URL = "http://localhost:8000"
FEEDBACK_CSV_PATH = Path("data/feedback_log.csv")


def test_thumbs_up_feedback():
    print("--- Testing POST /feedback (Thumbs Up) ---")
    payload = {
        "conversation_id": "conv-test-up-001",
        "query": "Can I patent traditional Ayurvedic knowledge?",
        "answer_snippet": "Under Section 3(p) of the Patents Act, 1970, traditional knowledge is non-patentable.",
        "citations": [
            {"source": "Patents Act, 1970", "section": "Section 3(p)"}
        ],
        "rating": "up",
        "comment": None,
    }
    req = urllib.request.Request(
        f"{BASE_URL}/feedback",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200, f"Expected 200, got {resp.status}"
        data = json.loads(resp.read().decode("utf-8"))
        print(f"  [OK] Response: {data}")
        assert data.get("status") == "ok"
        assert data.get("rating") == "up"
        assert data.get("feedback_id") is not None
        return data["feedback_id"]


def test_thumbs_down_feedback():
    print("\n--- Testing POST /feedback (Thumbs Down with Comment) ---")
    payload = {
        "conversation_id": "conv-test-down-002",
        "query": "What are the rules under Nagoya Protocol for TK?",
        "answer_snippet": "Article 5 addresses benefit-sharing.",
        "citations": [
            {"source": "Nagoya Protocol", "section": "Article 5"}
        ],
        "rating": "down",
        "comment": "missing citation for Article 7",
    }
    req = urllib.request.Request(
        f"{BASE_URL}/feedback",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200, f"Expected 200, got {resp.status}"
        data = json.loads(resp.read().decode("utf-8"))
        print(f"  [OK] Response: {data}")
        assert data.get("status") == "ok"
        assert data.get("rating") == "down"
        assert data.get("feedback_id") is not None
        return data["feedback_id"]


def test_invalid_rating_validation():
    print("\n--- Testing Rating Validation ---")
    payload = {
        "rating": "neutral",
        "query": "Test query",
    }
    req = urllib.request.Request(
        f"{BASE_URL}/feedback",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        urllib.request.urlopen(req)
        assert False, "Expected 400 or 422 error for invalid rating"
    except urllib.error.HTTPError as e:
        assert e.code in [400, 422], f"Expected 400 or 422, got {e.code}"
        print(f"  [OK] Successfully rejected invalid rating with status {e.code}")


def test_feedback_csv_logging(up_id: str, down_id: str):
    print("\n--- Testing Append-Only CSV Log (data/feedback_log.csv) ---")
    assert FEEDBACK_CSV_PATH.exists(), f"Log file {FEEDBACK_CSV_PATH} was not created"
    
    with open(FEEDBACK_CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"  [OK] Total rows in CSV log: {len(rows)}")
    row_ids = [r["id"] for r in rows]
    assert up_id in row_ids, f"Thumbs-up ID {up_id} not found in CSV"
    assert down_id in row_ids, f"Thumbs-down ID {down_id} not found in CSV"

    # Verify down row content
    down_row = next(r for r in rows if r["id"] == down_id)
    assert down_row["rating"] == "down"
    assert down_row["comment"] == "missing citation for Article 7"
    assert "Nagoya Protocol" in down_row["citations"]
    print(f"  [OK] Verified thumbs-down row in CSV: rating={down_row['rating']}, comment={down_row['comment']}")


def test_get_feedback_api(up_id: str, down_id: str):
    print("\n--- Testing GET /feedback Endpoint ---")
    req = urllib.request.Request(f"{BASE_URL}/feedback")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        entries = data.get("feedback", [])
        entry_ids = [e["id"] for e in entries]
        assert up_id in entry_ids, f"Thumbs-up ID {up_id} not found in GET /feedback"
        assert down_id in entry_ids, f"Thumbs-down ID {down_id} not found in GET /feedback"
        print(f"  [OK] Successfully retrieved {len(entries)} feedback entries via GET /feedback")


if __name__ == "__main__":
    import time
    # Ensure backend is warmed up
    for _ in range(10):
        try:
            r = urllib.request.urlopen(f"{BASE_URL}/health")
            if r.status == 200:
                break
        except Exception:
            time.sleep(2)

    up_id = test_thumbs_up_feedback()
    down_id = test_thumbs_down_feedback()
    test_invalid_rating_validation()
    test_feedback_csv_logging(up_id, down_id)
    test_get_feedback_api(up_id, down_id)
    print("\n=======================================================")
    print("ALL TESTS PASSED: Answer feedback mechanism fully verified!")
    print("=======================================================")
