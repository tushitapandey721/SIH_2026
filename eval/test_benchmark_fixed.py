"""Benchmark evaluation of retrieval fixes (sigmoid confidence + candidate pool depth)."""

import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

import torch
from app.retrieval.retrieve import LegalRetriever


def run_fixed_benchmark():
    print("=" * 80, flush=True)
    print("INITIALIZING FIXED LEGAL RETRIEVER (Sigmoid Calibrated + top_k=50)", flush=True)
    print("=" * 80, flush=True)

    retriever = LegalRetriever()

    # -------------------------------------------------------------------------
    # CHECK 1: Dense-Search Entry Rank Analysis for Section 3(p)
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80, flush=True)
    print("DENSE-SEARCH ENTRY RANK ANALYSIS FOR QUERY 1:", flush=True)
    print("Query: \"Is a classical Ayurvedic formulation patentable?\"", flush=True)
    print("=" * 80, flush=True)

    query_1 = "Is a classical Ayurvedic formulation patentable?"
    query_vec = retriever.embed_model.encode(query_1, normalize_embeddings=True, show_progress_bar=False).tolist()
    
    from qdrant_client.http.models import Filter, FieldCondition, MatchValue
    query_filter = Filter(must=[FieldCondition(key="jurisdiction", match=MatchValue(value="national"))])
    
    for pool_size in [20, 25, 30, 50]:
        resp = retriever.client.query_points(
            collection_name=retriever.collection_name,
            query=query_vec,
            query_filter=query_filter,
            limit=pool_size,
        )
        found_rank = None
        for r, pt in enumerate(resp.points, start=1):
            txt = pt.payload.get("text", "")
            title = pt.payload.get("title", "")
            if "Patents Act" in title and ("traditional knowledge" in txt.lower() or "3(p)" in txt or "CHAPTER II" in pt.payload.get("section", "")):
                found_rank = r
                break
        print(f"Pool size {pool_size:2d} -> Section 3(p) Patents Act entry rank: {found_rank if found_rank else 'NOT in top ' + str(pool_size)}", flush=True)

    # -------------------------------------------------------------------------
    # CHECK 2: Run the 3 Benchmark Queries
    # -------------------------------------------------------------------------
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
            "expected": "Biological Diversity Act / Rules content",
        },
    ]

    for item in queries:
        q_num = item["num"]
        q_text = item["query"]
        expected = item["expected"]

        print("\n" + "=" * 80, flush=True)
        print(f"BENCHMARK QUERY {q_num}: \"{q_text}\"", flush=True)
        print(f"EXPECTED: {expected}", flush=True)
        print("=" * 80, flush=True)

        start = time.perf_counter()
        results = retriever.retrieve(
            query=q_text,
            jurisdiction="national",
            top_k=50,
            rerank_top_k=3,
            score_threshold=0.35,
        )
        elapsed = (time.perf_counter() - start) * 1000

        print(f"Retrieved & reranked {len(results)} top passages in {elapsed:.2f} ms (all passing threshold >= 0.35):\n", flush=True)
        for rank, hit in enumerate(results, start=1):
            citation_prefix = hit.get("citation_prefix", "")
            section = hit.get("section", "")
            citation = f"{citation_prefix} {section}".strip()
            title = hit.get("title", "")
            dense_rank = hit.get("dense_rank", "N/A")
            dense_score = hit.get("dense_score", 0.0)
            score = hit.get("score", 0.0)
            text_snippet = hit.get("text", "").replace("\n", " ")[:260]

            print(f"  [Rank {rank}] Sigmoid Confidence: {score:.4f} ({score*100:.1f}%) | Dense Entry Rank: #{dense_rank} (Cosine: {dense_score:.4f})", flush=True)
            print(f"      Citation: {citation}", flush=True)
            print(f"      Document: {title}", flush=True)
            print(f"      Snippet:  {text_snippet}...\n", flush=True)

    print("=" * 80, flush=True)
    print("ALL 3 BENCHMARK QUERIES COMPLETED", flush=True)
    print("=" * 80, flush=True)


if __name__ == "__main__":
    run_fixed_benchmark()
