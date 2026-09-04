"""Regression test suite verifying FIX 1 (Section 2 definitions) and FIX 2 (Treaty Articles)."""

import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

from app.retrieval.retrieve import retrieve

TESTS = [
    # FIX 1: Patents Act Section 2 Definitions
    {
        "name": "Section 2(1)(ja) Inventive Step",
        "query": "what is an inventive step under the Patents Act?",
        "jurisdiction": "national",
        "expected_sec": "2(1)(ja)",
    },
    {
        "name": "Section 2(1)(j) Invention",
        "query": "what qualifies as an invention under the Patents Act?",
        "jurisdiction": "national",
        "expected_sec": "2(1)(j)",
    },
    {
        "name": "Section 2(1)(l) New Invention",
        "query": "what is a new invention under the Patents Act?",
        "jurisdiction": "national",
        "expected_sec": "2(1)(l)",
    },
    {
        "name": "Section 2(1)(ta) Pharmaceutical Substance",
        "query": "what is a pharmaceutical substance under the Patents Act?",
        "jurisdiction": "national",
        "expected_sec": "2(1)(ta)",
    },

    # FIX 2: International Treaty Articles
    {
        "name": "Nagoya Protocol Article 6",
        "query": "Article 6 Nagoya Protocol",
        "jurisdiction": "international",
        "expected_sec": "article 6",
    },
    {
        "name": "TRIPS Article 27",
        "query": "TRIPS Article 27 patentable subject matter",
        "jurisdiction": "international",
        "expected_sec": "article 27",
    },
    {
        "name": "CBD Article 15",
        "query": "CBD Article 15 access to genetic resources",
        "jurisdiction": "international",
        "expected_sec": "article 15",
    },
    {
        "name": "PCT Article 8",
        "query": "PCT Article 8 claiming priority",
        "jurisdiction": "international",
        "expected_sec": "article 8",
    },
]

print("=" * 80)
print("RUNNING FIX 1 & FIX 2 REGRESSION TESTS")
print("=" * 80)

passed = 0
for t in TESTS:
    res = retrieve(
        query=t["query"],
        jurisdiction=t["jurisdiction"],
        dense_top_k=60,
        bm25_top_k=30,
        fused_top_k=60,
        rerank_top_k=5,
        max_per_doc=3,
    )
    final_chunks = res.get("results", [])
    
    # Check if expected section is in top 5
    hit_rank = None
    for idx, c in enumerate(final_chunks, start=1):
        sec_str = str(c.get("section", "")).lower()
        if t["expected_sec"].lower() in sec_str:
            hit_rank = idx
            break

    status = f"PASS (Rank #{hit_rank})" if hit_rank else "FAIL (Not in Top 5)"
    if hit_rank:
        passed += 1
    print(f"• {t['name']:35} -> {status}")
    for idx, c in enumerate(final_chunks[:3], start=1):
        score_val = c.get('rerank_score', 0.0)
        print(f"    #{idx}: [{c.get('title', '')[:25]}] Section: {c.get('section', '')[:30]} | Score: {score_val:+.4f}")
    print("-" * 80)

print(f"\nREGRESSION TEST RESULT: {passed}/{len(TESTS)} PASSED")
