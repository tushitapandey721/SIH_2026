"""Complete step-by-step diagnostic script tracing the RAG retrieval flow."""

import sys
import os
import json
import time
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
from app.ingestion.manifest import load_manifest
from app.ingestion.extract import extract_document, locate_corpus_file


def run_full_diagnosis():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print("=" * 90, flush=True)
    print(f"STEP-BY-STEP RETRIEVAL PIPELINE DIAGNOSIS | Device: {device}", flush=True)
    print("=" * 90, flush=True)

    # -------------------------------------------------------------------------
    # 5. VERIFY EMBEDDING MODEL CONFIGURATION
    # -------------------------------------------------------------------------
    print("\n[CHECK 5] VERIFY EMBEDDING MODEL FOR INGESTION & QUERYING", flush=True)
    from app.retrieval import store, retrieve
    store_model = store.DEFAULT_MODEL_NAME
    retrieve_model = retrieve.DEFAULT_MODEL_NAME
    print(f"  • store.py DEFAULT_MODEL_NAME:    '{store_model}'", flush=True)
    print(f"  • retrieve.py DEFAULT_MODEL_NAME: '{retrieve_model}'", flush=True)
    assert store_model == retrieve_model == "BAAI/bge-m3", "Model mismatch detected!"
    print("  --> Verification: Both ingestion and query pipelines use identical 'BAAI/bge-m3' (1024 dimensions, cosine distance).", flush=True)

    # -------------------------------------------------------------------------
    # 6. PDF TEXT READABILITY & OCR AUDIT ACROSS CORPUS
    # -------------------------------------------------------------------------
    print("\n[CHECK 6] PDF READABILITY & OCR AUDIT (ALL 17 DOCUMENTS)", flush=True)
    manifest = load_manifest()
    print(f"  Loaded manifest with {len(manifest)} documents:")
    for idx, doc in enumerate(manifest, start=1):
        doc_id = doc.get("id") or doc.get("document_id")
        file_name = doc.get("filename") or doc.get("file_name")
        jurisdiction = doc.get("jurisdiction")
        title = doc.get("title", "")
        file_path = locate_corpus_file(file_name, jurisdiction)
        if not file_path or not file_path.exists():
            print(f"    [{idx:2d}] {doc_id} ({file_name}): MISSING FILE", flush=True)
            continue
        text, used_ocr = extract_document(file_path)
        print(f"    [{idx:2d}] {doc_id:12s} | Length: {len(text):7d} chars | OCR Used: {str(used_ocr):5s} | Title: {title[:45]}", flush=True)

    # -------------------------------------------------------------------------
    # 2. VECTOR DATABASE CONTENTS & COUNT
    # -------------------------------------------------------------------------
    print("\n[CHECK 2] VECTOR DATABASE CONTENTS & POINT COUNT", flush=True)
    client = QdrantClient(path=str(QDRANT_STORAGE_PATH))
    collection_info = client.get_collection(COLLECTION_NAME)
    total_points = collection_info.points_count
    print(f"  • Collection Name:      '{COLLECTION_NAME}'", flush=True)
    print(f"  • Total Stored Vectors: {total_points}", flush=True)
    print(f"  • Vector Dimensions:    {collection_info.config.params.vectors.size}", flush=True)
    print(f"  • Distance Metric:      {collection_info.config.params.vectors.distance}", flush=True)

    # Count by jurisdiction
    national_count = client.count(
        collection_name=COLLECTION_NAME,
        count_filter=Filter(must=[FieldCondition(key="jurisdiction", match=MatchValue(value="national"))]),
    ).count
    international_count = client.count(
        collection_name=COLLECTION_NAME,
        count_filter=Filter(must=[FieldCondition(key="jurisdiction", match=MatchValue(value="international"))]),
    ).count
    print(f"  • National Chunks:      {national_count}", flush=True)
    print(f"  • International Chunks: {international_count}", flush=True)

    # -------------------------------------------------------------------------
    # 3. FIRST 3 STORED CHUNKS WITH FULL METADATA
    # -------------------------------------------------------------------------
    print("\n[CHECK 3] FIRST 3 STORED CHUNKS WITH METADATA", flush=True)
    sample_scroll, _ = client.scroll(
        collection_name=COLLECTION_NAME,
        limit=3,
        with_payload=True,
        with_vectors=False,
    )
    for i, pt in enumerate(sample_scroll, start=1):
        p = pt.payload
        print(f"\n  --- Stored Chunk #{i} (ID: {pt.id}) ---", flush=True)
        print(f"      Title:           {p.get('title')}", flush=True)
        print(f"      Section:         {p.get('section')}", flush=True)
        print(f"      Citation Prefix: {p.get('citation_prefix')}", flush=True)
        print(f"      Jurisdiction:    '{p.get('jurisdiction')}'", flush=True)
        print(f"      Category:        {p.get('category')}", flush=True)
        print(f"      Authority:       {p.get('authority')}", flush=True)
        print(f"      Year:            {p.get('year')}", flush=True)
        print(f"      Text Preview:    {p.get('text', '')[:160].replace(chr(10), ' ')}...", flush=True)

    # -------------------------------------------------------------------------
    # 4. TOP 10 RETRIEVED CHUNKS BEFORE RERANKING
    # -------------------------------------------------------------------------
    test_query = "Is a classical Ayurvedic formulation patentable?"
    print("\n" + "=" * 90, flush=True)
    print(f"[CHECK 4] TOP 10 DENSE RETRIEVED CHUNKS BEFORE RERANKING", flush=True)
    print(f"Query: \"{test_query}\"", flush=True)
    print(f"Jurisdiction Filter: 'national'", flush=True)
    print("=" * 90, flush=True)

    embed_model = SentenceTransformer(DEFAULT_MODEL_NAME, device=device)
    embed_model.max_seq_length = 512
    q_vec = embed_model.encode(test_query, normalize_embeddings=True, show_progress_bar=False).tolist()

    resp = client.query_points(
        collection_name=COLLECTION_NAME,
        query=q_vec,
        query_filter=Filter(must=[FieldCondition(key="jurisdiction", match=MatchValue(value="national"))]),
        limit=10,
    )

    print(f"Top 10 Dense Results from Qdrant (Cosine Similarity):", flush=True)
    for rank, hit in enumerate(resp.points, start=1):
        p = hit.payload
        print(f"\n  [Rank {rank:2d}] Cosine Score: {hit.score:.4f}", flush=True)
        print(f"      Document: {p.get('title')}", flush=True)
        print(f"      Citation: {p.get('citation_prefix')} {p.get('section')}", flush=True)
        print(f"      Category: {p.get('category')}", flush=True)
        print(f"      Text:     {p.get('text', '')[:180].replace(chr(10), ' ')}...", flush=True)

    # -------------------------------------------------------------------------
    # 7. SECTION 3(p) PROVENANCE & CROSS-ENCODER RERANKING
    # -------------------------------------------------------------------------
    print("\n" + "=" * 90, flush=True)
    print("[CHECK 7] SECTION 3(p) PROVENANCE & CROSS-ENCODER RERANKING", flush=True)
    print("=" * 90, flush=True)

    resp_60 = client.query_points(
        collection_name=COLLECTION_NAME,
        query=q_vec,
        query_filter=Filter(must=[FieldCondition(key="jurisdiction", match=MatchValue(value="national"))]),
        limit=60,
    )

    sec3p_hit = None
    sec3p_dense_rank = None
    for r, hit in enumerate(resp_60.points, start=1):
        p = hit.payload
        if p.get("title") == "Patents Act 1970" and "3(p)" in p.get("section", ""):
            sec3p_hit = hit
            sec3p_dense_rank = r
            break

    if sec3p_hit:
        print(f"  • Section 3(p) Found at Dense Rank: #{sec3p_dense_rank} (Cosine: {sec3p_hit.score:.4f})", flush=True)
        print(f"    Citation: Patents Act {sec3p_hit.payload.get('section')}", flush=True)
        print(f"    Text:     {sec3p_hit.payload.get('text')}", flush=True)
    else:
        print("  • Section 3(p) was not found in top 60.", flush=True)

    # Evaluate reranking on the top 10 candidates + Section 3(p)
    snapshot_path = snapshot_download("BAAI/bge-reranker-v2-m3")
    reranker = CrossEncoder(snapshot_path, device=device)
    
    candidates = [hit.payload for hit in resp.points]
    if sec3p_hit and sec3p_hit.payload not in candidates:
        candidates.append(sec3p_hit.payload)

    pairs = [[test_query, c["text"][:600]] for c in candidates]
    start_rerank = time.perf_counter()
    raw_logits = reranker.predict(pairs, batch_size=16, show_progress_bar=False)
    rerank_time = (time.perf_counter() - start_rerank) * 1000
    
    sigmoid_scores = torch.sigmoid(torch.tensor(raw_logits, dtype=torch.float32)).tolist()
    for c, logit, sig in zip(candidates, raw_logits, sigmoid_scores):
        c["rerank_logit"] = float(logit)
        c["rerank_sigmoid"] = float(sig)

    reranked = sorted(candidates, key=lambda x: x["rerank_sigmoid"], reverse=True)
    print(f"\nReranked Results (evaluated {len(candidates)} pairs in {rerank_time:.2f} ms):", flush=True)
    for r, c in enumerate(reranked[:5], start=1):
        print(f"  [Rank {r}] Sigmoid Confidence: {c['rerank_sigmoid']:.4f} ({c['rerank_sigmoid']*100:.1f}%) | Raw Logit: {c['rerank_logit']:+.4f} | Citation: {c.get('citation_prefix')} {c.get('section')} | Doc: {c.get('title')}", flush=True)

    print("\n" + "=" * 90, flush=True)


if __name__ == "__main__":
    run_full_diagnosis()
