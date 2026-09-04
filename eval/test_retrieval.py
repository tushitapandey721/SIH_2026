"""Evaluation script to test LegalRetriever against 3 benchmark queries with jurisdiction='national'."""

import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

import torch
from app.retrieval.retrieve import LegalRetriever


def run_retrieval_benchmark():
    retriever = LegalRetriever()

    queries = [
        {
            "num": 1,
            "query": "Is a classical Ayurvedic formulation patentable?",
            "expected": "Section 3(p) of the Patents Act 1970",
        },
        {
            "num": 2,
            "query": "What proof is required to classify something as a new ASU drug rather than a classical formulation?",
            "expected": "Rule 158-B from the Drugs and Cosmetics Rules",
        },
        {
            "num": 3,
            "query": "Does an Ayurvedic company need approval before using a biological resource collected in India?",
            "expected": "Biological Diversity Act / Rules (Section 3 / Section 7 / Rule 14/15)",
        },
    ]

    for item in queries:
        q_num = item["num"]
        q_text = item["query"]
        expected = item["expected"]

        print("\n" + "=" * 80, flush=True)
        print(f"QUERY {q_num}: \"{q_text}\"", flush=True)
        print(f"EXPECTED SOURCE: {expected}", flush=True)
        print("=" * 80, flush=True)

        start = time.perf_counter()
        results = retriever.retrieve(
            query=q_text,
            jurisdiction="national",
            top_k=15,
            rerank_top_k=3,
            score_threshold=-100.0,
        )
        elapsed = (time.perf_counter() - start) * 1000

        print(f"Retrieved & reranked top {len(results)} results in {elapsed:.2f} ms:\n", flush=True)
        for rank, hit in enumerate(results, start=1):
            citation_prefix = hit.get("citation_prefix", "")
            section = hit.get("section", "")
            citation = f"{citation_prefix} {section}".strip()
            title = hit.get("title", "")
            score = hit.get("rerank_score", 0.0)
            text_snippet = hit.get("text", "").replace("\n", " ")[:250]

            print(f"  [Rank {rank}] Score: {score:+.4f} | Citation: {citation}", flush=True)
            print(f"      Document: {title}", flush=True)
            print(f"      Snippet:  {text_snippet}...\n", flush=True)

    print("=" * 80, flush=True)
    print("ALL 3 BENCHMARK QUERIES COMPLETED", flush=True)
    print("=" * 80, flush=True)


if __name__ == "__main__":
    run_retrieval_benchmark()
