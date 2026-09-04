"""Diagnostic script to debug Qdrant retrieval, filters, embeddings, and reranker scores step-by-step."""

import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

import torch
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer, CrossEncoder
from huggingface_hub import snapshot_download

from app.retrieval.store import COLLECTION_NAME, QDRANT_STORAGE_PATH, DEFAULT_MODEL_NAME


def run_diagnostics():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print("=" * 80)
    print(f"RETRIEVAL PIPELINE DIAGNOSTIC REPORT | Device: {device}")
    print("=" * 80)

    client = QdrantClient(path=str(QDRANT_STORAGE_PATH))
    embed_model = SentenceTransformer(DEFAULT_MODEL_NAME, device=device)
    embed_model.max_seq_length = 512

    snapshot_path = snapshot_download("BAAI/bge-reranker-v2-m3")
    rerank_model = CrossEncoder(snapshot_path, device=device)
    rerank_model.max_length = 512
    if hasattr(rerank_model, "tokenizer"):
        rerank_model.tokenizer.model_max_length = 512

    test_query = "Is a classical Ayurvedic formulation patentable?"

    # -------------------------------------------------------------------------
    # STEP 2: Inspect raw points and jurisdiction payload field values
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("STEP 2: Sample Point Inspection (Checking 'jurisdiction' Field Values)")
    print("=" * 80)
    
    sample_points, _ = client.scroll(
        collection_name=COLLECTION_NAME,
        limit=10,
        with_payload=True,
        with_vectors=False,
    )
    print(f"Sampled {len(sample_points)} points from Qdrant:")
    for pt in sample_points:
        p = pt.payload
        print(f"  • Point ID: {pt.id}")
        print(f"    - Title:        {p.get('title')}")
        print(f"    - Section:      {p.get('section')}")
        print(f"    - Jurisdiction: '{p.get('jurisdiction')}' (type: {type(p.get('jurisdiction')).__name__})")
        print(f"    - Category:     '{p.get('category')}'")

    # -------------------------------------------------------------------------
    # STEP 1: Unfiltered Raw Dense Search
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print(f"STEP 1: Raw Dense Search (NO FILTER) for: \"{test_query}\"")
    print("=" * 80)

    query_vec = embed_model.encode(test_query, normalize_embeddings=True, show_progress_bar=False).tolist()

    unfiltered_resp = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vec,
        limit=5,
    )

    print("Top 5 Unfiltered Results from Qdrant:")
    for idx, hit in enumerate(unfiltered_resp.points, start=1):
        p = hit.payload
        print(f"\n  [{idx}] Raw Cosine Score: {hit.score:.4f}")
        print(f"      Jurisdiction: '{p.get('jurisdiction')}'")
        print(f"      Title:        {p.get('title')}")
        print(f"      Citation:     {p.get('citation_prefix')} {p.get('section')}")
        print(f"      Snippet:      {p.get('text', '')[:200].replace(chr(10), ' ')}...")

    # -------------------------------------------------------------------------
    # STEP 3: Filter Object Inspection & Filtered Search
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("STEP 3: Filter Object Inspection (retrieve() filter syntax)")
    print("=" * 80)

    filter_obj = Filter(must=[FieldCondition(key="jurisdiction", match=MatchValue(value="national"))])
    print("Exact Filter Object sent to Qdrant:")
    print(f"  Python Repr: {filter_obj}")
    print(f"  JSON Dict:   {json.dumps(filter_obj.model_dump(), indent=2)}")

    filtered_resp = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vec,
        query_filter=filter_obj,
        limit=5,
    )

    print(f"\nFiltered Query returned {len(filtered_resp.points)} points:")
    for idx, hit in enumerate(filtered_resp.points, start=1):
        p = hit.payload
        print(f"  [{idx}] Dense Score: {hit.score:.4f} | Citation: {p.get('citation_prefix')} {p.get('section')} | Doc: {p.get('title')}")

    # -------------------------------------------------------------------------
    # STEP 4: Dense vs Cross-Encoder Rerank Scores Comparison
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("STEP 4: Dense vs Cross-Encoder Rerank Scores Comparison")
    print("=" * 80)

    candidates = [hit.payload for hit in filtered_resp.points if hit.payload]
    pairs = [[test_query, c["text"][:1000]] for c in candidates]
    rerank_scores = rerank_model.predict(pairs, batch_size=16, show_progress_bar=False)

    for idx, (cand, dense_hit, r_score) in enumerate(zip(candidates, filtered_resp.points, rerank_scores), start=1):
        sigmoid_score = 1.0 / (1.0 + float(torch.exp(-torch.tensor(float(r_score)))))
        cand["rerank_raw_logit"] = float(r_score)
        cand["rerank_sigmoid"] = float(sigmoid_score)

        print(f"\n  Result [{idx}]:")
        print(f"    • Citation:         {cand.get('citation_prefix')} {cand.get('section')}")
        print(f"    • Title:            {cand.get('title')}")
        print(f"    • Dense Cosine:     {dense_hit.score:.4f}")
        print(f"    • Rerank Raw Logit: {cand['rerank_raw_logit']:+.4f}")
        print(f"    • Rerank Sigmoid:   {cand['rerank_sigmoid']:.4f}")

    # -------------------------------------------------------------------------
    # STEP 5: Threshold Analysis (0.35 threshold vs actual scores)
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("STEP 5: Threshold Analysis & Abstention Diagnostic")
    print("=" * 80)
    
    current_threshold = 0.35
    top_raw_logit = max(c["rerank_raw_logit"] for c in candidates)
    top_sigmoid = max(c["rerank_sigmoid"] for c in candidates)

    print(f"Configured Threshold:              {current_threshold}")
    print(f"Actual Top Raw Logit:             {top_raw_logit:+.4f}")
    print(f"Actual Top Sigmoid (0.0 to 1.0):   {top_sigmoid:.4f}")

    if top_raw_logit < current_threshold and top_sigmoid >= current_threshold:
        print("\n--> CRITICAL FINDING: Raw logit vs Sigmoid discrepancy!")
        print("    The cross-encoder outputs raw unbounded logits (which can be < 0.35 even for good matches).")
        print("    If threshold 0.35 expects a 0-1 probability, sigmoid must be applied to the logit, or threshold adjusted!")
    elif top_raw_logit >= current_threshold:
        print("\n--> Top raw logit passes threshold!")

    print("=" * 80)


if __name__ == "__main__":
    run_diagnostics()
