"""Debug retrieval for Section 2(1)(ja) query step by step."""

import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

from app.retrieval.retrieve import get_default_retriever
from app.retrieval.query_expansion import expand_legal_query

retriever = get_default_retriever()
query = "what is an inventive step under the Patents Act?"
norm_q, exp_q = expand_legal_query(query)
print("Original query:", query)
print("Normalized query:", norm_q)
print("Expanded query:", exp_q)

# Check BM25 search
bm25_hits = retriever.bm25_index.search(norm_q, jurisdiction="national", top_k=10)
print(f"\n--- BM25 Top 5 for norm_q ---")
for h in bm25_hits[:5]:
    print(f"  • Rank {h.get('bm25_rank')}: [{h.get('title')}] {h.get('section')} (Score: {h.get('bm25_score'):.2f})")

# Check BM25 search for exp_q
bm25_exp_hits = retriever.bm25_index.search(exp_q, jurisdiction="national", top_k=10)
print(f"\n--- BM25 Top 5 for exp_q ---")
for h in bm25_exp_hits[:5]:
    print(f"  • Rank {h.get('bm25_rank')}: [{h.get('title')}] {h.get('section')} (Score: {h.get('bm25_score'):.2f})")

# Check Full Retrieve
results, diag = retriever.retrieve(query, jurisdiction="national", dense_top_k=60, bm25_top_k=30, fused_top_k=60, rerank_top_k=5)
print(f"\n--- Final Top 5 from retrieve() ---")
for idx, r in enumerate(results, start=1):
    print(f"  #{idx}: [{r.get('title')}] Section: {r.get('section')} | CE Score: {r.get('cross_encoder_raw_score'):+.4f}")
