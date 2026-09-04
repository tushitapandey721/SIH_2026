"""Benchmark script for CrossEncoder FP16 optimization, candidate reduction, and batch size sweep."""

import sys
import os
import time
import json
from pathlib import Path

# Ensure UTF-8 output on Windows
if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import torch
from sentence_transformers import SentenceTransformer, CrossEncoder
from huggingface_hub import snapshot_download
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue

from app.retrieval.store import COLLECTION_NAME, QDRANT_STORAGE_PATH, DEFAULT_MODEL_NAME
from app.retrieval.bm25 import BM25Index
from app.retrieval.query_expansion import expand_legal_query
from app.llm.client import get_completion
from app.llm.prompts import SYSTEM_PROMPT


def run_benchmark():
    print("=" * 90)
    print("      CROSS-ENCODER FP16 + FUSED_TOP_K=12 + MAX_LENGTH=256 BENCHMARK SUITE")
    print("=" * 90)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Device: {device.upper()}")
    if device == "cuda":
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats()
        print(f"GPU Model: {torch.cuda.get_device_name(0)}")
        print(f"Initial VRAM Allocated: {torch.cuda.memory_allocated(0)/(1024*1024):.2f} MB")

    # 1. Initialize Client & BM25
    client = QdrantClient(path=str(QDRANT_STORAGE_PATH))
    bm25_index = BM25Index()
    points, _ = client.scroll(collection_name=COLLECTION_NAME, limit=5000, with_payload=True, with_vectors=False)
    bm25_index.build_from_qdrant_points(points)

    # 2. Load BGE-M3 (FP16 on CUDA)
    t_embed_load_start = time.perf_counter()
    embed_model = SentenceTransformer(
        DEFAULT_MODEL_NAME,
        device=device,
        model_kwargs={"torch_dtype": torch.float16} if device == "cuda" else {},
    )
    embed_model.max_seq_length = 512
    t_embed_load = (time.perf_counter() - t_embed_load_start) * 1000
    embed_dtype = next(embed_model.parameters()).dtype

    # 3. Load CrossEncoder (FP16 on CUDA via model_kwargs)
    t_rerank_load_start = time.perf_counter()
    rerank_model = CrossEncoder(
        "BAAI/bge-reranker-v2-m3",
        device=device,
        max_length=256,
        model_kwargs={"torch_dtype": torch.float16} if device == "cuda" else {},
    )
    t_rerank_load = (time.perf_counter() - t_rerank_load_start) * 1000
    rerank_dtype = next(rerank_model.model.parameters()).dtype

    print(f"\nModel Initialization Complete:")
    print(f"  • BGE-M3 Embedder Dtype   : {embed_dtype} (Load time: {t_embed_load:.1f} ms)")
    print(f"  • CrossEncoder Dtype      : {rerank_dtype} (Load time: {t_rerank_load:.1f} ms)")
    if device == "cuda":
        print(f"  • VRAM Allocated Post-Load: {torch.cuda.memory_allocated(0)/(1024*1024):.2f} MB")
        print(f"  • VRAM Reserved Post-Load : {torch.cuda.memory_reserved(0)/(1024*1024):.2f} MB")

    # Helper for retrieval pipeline with configurable batch_size and fused_top_k
    def execute_pipeline(query: str, fused_top_k: int = 12, batch_size: int = 16):
        t0 = time.perf_counter()

        # Step 1: Expand query
        t_exp_s = time.perf_counter()
        norm_query, expanded_query = expand_legal_query(query)
        t_exp_ms = (time.perf_counter() - t_exp_s) * 1000

        # Step 2: Dense retrieve
        t_dense_s = time.perf_counter()
        with torch.inference_mode():
            query_vector = embed_model.encode(expanded_query, normalize_embeddings=True, show_progress_bar=False).tolist()
        query_filter = Filter(must=[FieldCondition(key="jurisdiction", match=MatchValue(value="national"))])
        dense_hits = client.query_points(collection_name=COLLECTION_NAME, query=query_vector, query_filter=query_filter, limit=30).points
        dense_candidates = {str(h.id): dict(h.payload, id=str(h.id), dense_rank=r, dense_score=float(h.score)) for r, h in enumerate(dense_hits, 1) if h.payload}
        t_dense_ms = (time.perf_counter() - t_dense_s) * 1000

        # Step 3: Sparse retrieve
        t_bm25_s = time.perf_counter()
        bm25_hits = bm25_index.search(query=norm_query, jurisdiction="national", top_k=20)
        bm25_candidates = {str(h.get("id")): h for h in bm25_hits}
        if norm_query != expanded_query:
            for h in bm25_index.search(query=expanded_query, jurisdiction="national", top_k=20):
                did = str(h.get("id"))
                if did not in bm25_candidates:
                    bm25_candidates[did] = dict(h, bm25_rank=len(bm25_candidates) + 1)
        t_bm25_ms = (time.perf_counter() - t_bm25_s) * 1000

        # Step 4: RRF Fusion
        t_rrf_s = time.perf_counter()
        all_ids = set(dense_candidates.keys()).union(set(bm25_candidates.keys()))
        fused = []
        for did in all_ids:
            c = dict(dense_candidates[did]) if did in dense_candidates else dict(bm25_candidates[did])
            dr = dense_candidates.get(did, {}).get("dense_rank")
            br = bm25_candidates.get(did, {}).get("bm25_rank")
            c["dense_rank"] = dr
            c["bm25_rank"] = br
            rrf_score = (1.0 / (60 + dr) if dr else 0.0) + (1.0 / (60 + br) if br else 0.0)
            c["rrf_score"] = float(rrf_score)
            fused.append(c)
        fused.sort(key=lambda x: x["rrf_score"], reverse=True)
        selected_candidates = fused[:fused_top_k]
        t_rrf_ms = (time.perf_counter() - t_rrf_s) * 1000

        # Step 5: CrossEncoder Rerank
        t_ce_s = time.perf_counter()
        pairs = [[expanded_query, f"{c.get('title', '')} {c.get('citation_prefix', '')} {c.get('section', '')}: {c.get('text', '')}"[:750]] for c in selected_candidates]
        with torch.inference_mode():
            raw_logits = rerank_model.predict(pairs, batch_size=batch_size, max_length=256, show_progress_bar=False)
        sigmoids = torch.sigmoid(torch.tensor(raw_logits, dtype=torch.float32)).tolist()
        for c, raw, sig in zip(selected_candidates, raw_logits, sigmoids):
            c["cross_encoder_raw_score"] = float(raw)
            c["score"] = float(raw)
            c["cross_encoder_sigmoid"] = float(sig)
        reranked_pool = sorted(selected_candidates, key=lambda x: x["cross_encoder_raw_score"], reverse=True)

        # Diverse Top-5
        diverse_top_k = []
        doc_counts = {}
        for c in reranked_pool:
            title = c.get("title", "")
            if doc_counts.get(title, 0) < 3:
                diverse_top_k.append(c)
                doc_counts[title] = doc_counts.get(title, 0) + 1
            if len(diverse_top_k) == 5:
                break
        if len(diverse_top_k) < 5:
            for c in reranked_pool:
                if c not in diverse_top_k:
                    diverse_top_k.append(c)
                if len(diverse_top_k) == 5:
                    break
        t_ce_ms = (time.perf_counter() - t_ce_s) * 1000

        total_retrieval_ms = (time.perf_counter() - t0) * 1000
        return diverse_top_k, {
            "query_expansion_ms": t_exp_ms,
            "dense_ms": t_dense_ms,
            "bm25_ms": t_bm25_ms,
            "rrf_ms": t_rrf_ms,
            "cross_encoder_ms": t_ce_ms,
            "total_retrieval_ms": total_retrieval_ms,
            "pairs_evaluated": len(pairs),
        }

    # -------------------------------------------------------------------------
    # PART A: BATCH SIZE SWEEP (4, 8, 16, 32) on Query 1
    # -------------------------------------------------------------------------
    print("\n" + "=" * 90)
    print("PART A: CROSS-ENCODER BATCH SIZE SWEEP (Query: 'What does Section 3(p) of the Patents Act prohibit?')")
    print("=" * 90)
    test_q1 = "What does Section 3(p) of the Patents Act prohibit?"
    batch_sizes = [4, 8, 16, 32]
    best_bs = 16
    min_ce_latency = float("inf")

    # Warmup run
    _, _ = execute_pipeline(test_q1, fused_top_k=12, batch_size=16)

    for bs in batch_sizes:
        if device == "cuda":
            torch.cuda.reset_peak_memory_stats()
        results, timings = execute_pipeline(test_q1, fused_top_k=12, batch_size=bs)
        peak_vram_mb = torch.cuda.max_memory_allocated(0)/(1024*1024) if device == "cuda" else 0.0
        ce_ms = timings["cross_encoder_ms"]
        print(f"Batch Size {bs:2d} -> CE Latency: {ce_ms:7.2f} ms | Peak VRAM: {peak_vram_mb:.2f} MB | Pairs: {timings['pairs_evaluated']}")
        if ce_ms < min_ce_latency:
            min_ce_latency = ce_ms
            best_bs = bs

    print(f"\n--> Selected Optimal Batch Size: {best_bs} (Fastest stable CE inference: {min_ce_latency:.2f} ms)")

    # -------------------------------------------------------------------------
    # PART B: BENCHMARK PRIMARY QUERY WITH LLM END-TO-END
    # -------------------------------------------------------------------------
    print("\n" + "=" * 90)
    print(f"PART B: END-TO-END BENCHMARK ON PRIMARY QUERY ('{test_q1}')")
    print("=" * 90)
    top_5, timings = execute_pipeline(test_q1, fused_top_k=12, batch_size=best_bs)

    # Prompt construction & LLM Call
    t_llm_s = time.perf_counter()
    context_lines = [f"--- Source [{i}] ---\nAct: {c.get('title')}\nSection: {c.get('section')}\nContent: {c.get('text')}" for i, c in enumerate(top_5, 1)]
    user_prompt = f"User Inquiry: {test_q1}\nClassified Category: classical_medicine\n\nRETRIEVED CONTEXT:\n" + "\n\n".join(context_lines)
    llm_res = get_completion(system_prompt=SYSTEM_PROMPT, user_prompt=user_prompt, max_tokens=1024)
    t_llm_ms = (time.perf_counter() - t_llm_s) * 1000
    total_e2e_ms = timings["total_retrieval_ms"] + t_llm_ms

    print("\n--- TIMING BREAKDOWN (AFTER OPTIMIZATION) ---")
    print(f"Query expansion:        {timings['query_expansion_ms']:8.2f} ms")
    print(f"BGE-M3 embedding:       {timings['dense_ms']:8.2f} ms")
    print(f"BM25 retrieval:         {timings['bm25_ms']:8.2f} ms")
    print(f"RRF fusion:             {timings['rrf_ms']:8.2f} ms")
    print(f"CrossEncoder rerank:    {timings['cross_encoder_ms']:8.2f} ms  <-- (Was 78,516.98 ms)")
    print(f"LLM API Generation:     {t_llm_ms:8.2f} ms  (Groq {llm_res.get('provider_used')})")
    print("-" * 90)
    print(f"Total Retrieval Time:   {timings['total_retrieval_ms']:8.2f} ms")
    print(f"Total End-to-End Time:  {total_e2e_ms:8.2f} ms  ({total_e2e_ms/1000:.2f} seconds!)")

    print("\n--- TOP-5 RETRIEVAL PASSAGES & SECTION 3(p) QUALITY CHECK ---")
    found_3p = False
    rank_3p = None
    for r, c in enumerate(top_5, 1):
        sec = c.get("section", "")
        title = c.get("title", "")
        score = c.get("score", 0.0)
        is_3p = "3(p)" in sec or "3(p)" in c.get("text", "")
        marker = " [CRITICAL MATCH: Section 3(p)]" if is_3p else ""
        print(f"  Rank {r}: [{title}] {sec} | CE Score: {score:+.4f}{marker}")
        if is_3p and not found_3p:
            found_3p = True
            rank_3p = r

    assert found_3p, "CRITICAL FAILURE: Section 3(p) was lost from Top-5!"
    print(f"\n[QUALITY VERIFIED] Section 3(p) is present at Rank {rank_3p} in Top-5!")

    # -------------------------------------------------------------------------
    # PART C: BENCHMARK 3 ADDITIONAL REQUISITE TEST QUERIES
    # -------------------------------------------------------------------------
    print("\n" + "=" * 90)
    print("PART C: BENCHMARK 3 ADDITIONAL LEGAL INQUIRIES")
    print("=" * 90)

    additional_queries = [
        "Can traditional knowledge be patented under Section 3(p)?",
        "Is a classical Ayurvedic formulation patentable?",
        "Is an invention based on known Ayurvedic properties patentable?",
    ]

    for q_idx, q_text in enumerate(additional_queries, 1):
        print(f"\n--- Query {q_idx}: '{q_text}' ---")
        top_res, q_timings = execute_pipeline(q_text, fused_top_k=12, batch_size=best_bs)
        print(f"  Retrieval Latency : {q_timings['total_retrieval_ms']:.2f} ms (CrossEncoder: {q_timings['cross_encoder_ms']:.2f} ms)")
        print(f"  Top 3 Passages:")
        for r, c in enumerate(top_res[:3], 1):
            print(f"    Rank {r}: [{c.get('title')}] {c.get('section')} (Score: {c.get('score'):+.4f})")

    print("\n" + "=" * 90)
    print("ALL BENCHMARKS COMPLETED SUCCESSFULLY!")
    print("=" * 90)


if __name__ == "__main__":
    run_benchmark()
