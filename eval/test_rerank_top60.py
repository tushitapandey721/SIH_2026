"""Test CrossEncoder reranking of top 60 national candidates for Query 1."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

import torch
from app.retrieval.retrieve import LegalRetriever

retriever = LegalRetriever()

query = "Is a classical Ayurvedic formulation patentable?"
print("=" * 80)
print(f"QUERY: \"{query}\"")
print("Evaluating top_k=60 dense candidate pool with CrossEncoder reranker...")
print("=" * 80)

results = retriever.retrieve(
    query=query,
    jurisdiction="national",
    top_k=60,
    rerank_top_k=5,
    score_threshold=0.35,
)

print(f"\nTop {len(results)} reranked results (with sigmoid confidence):")
for rank, hit in enumerate(results, start=1):
    citation = f"{hit.get('citation_prefix')} {hit.get('section')}".strip()
    score = hit.get("score", 0.0)
    dense_rank = hit.get("dense_rank", "N/A")
    title = hit.get("title", "")
    snippet = hit.get("text", "").replace("\n", " ")[:220]

    print(f"\n  [Rank {rank}] Sigmoid Confidence: {score:.4f} ({score*100:.1f}%) | Dense Entry Rank: #{dense_rank}")
    print(f"      Citation: {citation}")
    print(f"      Document: {title}")
    print(f"      Snippet:  {snippet}...")
