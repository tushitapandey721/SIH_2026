"""Hybrid legal retrieval pipeline combining BGE-M3, BM25, RRF, and Cross-Encoder reranking."""

import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import torch
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer, CrossEncoder
from huggingface_hub import snapshot_download

from app.retrieval.store import COLLECTION_NAME, QDRANT_STORAGE_PATH, DEFAULT_MODEL_NAME
from app.retrieval.bm25 import BM25Index
from app.retrieval.query_expansion import expand_legal_query

# Pipeline Configuration
DENSE_TOP_K = 30
BM25_TOP_K = 20
RRF_K = 60
FUSED_TOP_K = 12
RERANK_TOP_K = 5
RERANK_MAX_LENGTH = 256
RERANK_BATCH_SIZE = 8
BM25_CACHE_FILENAME = "bm25_cache.pkl.gz"


def get_device() -> str:
    """Detects available hardware acceleration (CUDA vs CPU).
    Falls back to CPU if running in Hugging Face ZeroGPU or if FORCE_CPU is enabled.
    """
    if os.getenv("SPACES_ZERO_GPU") == "true" or os.getenv("FORCE_CPU") == "1":
        return "cpu"
    device = "cuda" if torch.cuda.is_available() else "cpu"
    return device


class LegalRetriever:
    """Hybrid Legal Retriever implementing Dense (BGE-M3) + Sparse (BM25) + RRF + CrossEncoder in FP16."""

    def __init__(
        self,
        storage_path: Optional[str | Path] = None,
        embed_model_name: str = DEFAULT_MODEL_NAME,
        rerank_model_name: str = "BAAI/bge-reranker-v2-m3",
        collection_name: str = COLLECTION_NAME,
        batch_size: int = RERANK_BATCH_SIZE,
    ):
        self.device = get_device()
        self.storage_path = Path(storage_path) if storage_path else QDRANT_STORAGE_PATH
        self.collection_name = collection_name
        self.batch_size = batch_size
        self.cache_path = self.storage_path / BM25_CACHE_FILENAME

        lock_path = self.storage_path / ".lock"
        if lock_path.exists():
            try:
                lock_path.unlink()
            except Exception:
                pass
        self.client = QdrantClient(path=str(self.storage_path))

        # 1. Load BGE-M3 (FP16 on CUDA)
        try:
            self.embed_model = SentenceTransformer(
                embed_model_name,
                device=self.device,
                local_files_only=True,
                model_kwargs={"torch_dtype": torch.float16} if self.device == "cuda" else {},
            )
        except Exception:
            self.embed_model = SentenceTransformer(
                embed_model_name,
                device=self.device,
                model_kwargs={"torch_dtype": torch.float16} if self.device == "cuda" else {},
            )
        self.embed_model.max_seq_length = 512

        # 2. Load CrossEncoder (FP16 on CUDA via model_kwargs)
        try:
            snapshot_path = snapshot_download(rerank_model_name, local_files_only=True)
            self.rerank_model = CrossEncoder(
                snapshot_path,
                device=self.device,
                max_length=RERANK_MAX_LENGTH,
                local_files_only=True,
                model_kwargs={"torch_dtype": torch.float16} if self.device == "cuda" else {},
            )
        except Exception:
            try:
                self.rerank_model = CrossEncoder(
                    rerank_model_name,
                    device=self.device,
                    max_length=RERANK_MAX_LENGTH,
                    local_files_only=True,
                    model_kwargs={"torch_dtype": torch.float16} if self.device == "cuda" else {},
                )
            except Exception:
                self.rerank_model = CrossEncoder(
                    rerank_model_name,
                    device=self.device,
                    max_length=RERANK_MAX_LENGTH,
                    model_kwargs={"torch_dtype": torch.float16} if self.device == "cuda" else {},
                )

        embed_dtype = next(self.embed_model.parameters()).dtype if hasattr(self.embed_model, "parameters") else "unknown"
        rerank_dtype = next(self.rerank_model.model.parameters()).dtype if hasattr(self.rerank_model, "model") else "unknown"
        print(f"[Hardware Acceleration] Device: {self.device.upper()} | Embed Dtype: {embed_dtype} | Rerank Dtype: {rerank_dtype}")

        # Initialize and build BM25 index from disk cache or Qdrant
        self.bm25_index = BM25Index()
        self._build_bm25_index()

    def _build_bm25_index(self, force_rebuild: bool = False) -> None:
        """Loads or builds the BM25 index, using a compressed disk cache if available."""
        if not force_rebuild and self.cache_path.exists():
            try:
                t0 = time.perf_counter()
                self.bm25_index = BM25Index.load_from_disk(self.cache_path)
                load_ms = (time.perf_counter() - t0) * 1000
                total_docs = sum(self.bm25_index.total_docs_by_jurisdiction.values())
                if total_docs > 0:
                    print(f"[BM25 Cache] Loaded {total_docs} statutory chunks from disk cache in {load_ms:.2f}ms: {self.cache_path}")
                    return
            except Exception as e:
                print(f"[BM25 Cache] Failed to load cache ({e}). Rebuilding from Qdrant...")

        # Ensure collection exists; if missing, trigger automated corpus ingestion
        try:
            existing_collections = [c.name for c in self.client.get_collections().collections]
        except Exception:
            existing_collections = []

        if self.collection_name not in existing_collections:
            print(f"[Qdrant] Collection '{self.collection_name}' not found. Triggering automated corpus ingestion...")
            try:
                from app.retrieval.store import ingest_all
                ingest_all()
            except Exception as e:
                print(f"[Qdrant] Ingestion warning: {e}")

        # Rebuild from Qdrant scroll
        t0 = time.perf_counter()
        try:
            points, _ = self.client.scroll(
                collection_name=self.collection_name,
                limit=5000,
                with_payload=True,
                with_vectors=False,
            )
        except Exception as e:
            print(f"[Qdrant] Could not scroll collection '{self.collection_name}': {e}")
            points = []

        self.bm25_index = BM25Index()
        self.bm25_index.build_from_qdrant_points(points)
        build_ms = (time.perf_counter() - t0) * 1000
        total_docs = sum(self.bm25_index.total_docs_by_jurisdiction.values())
        print(f"[BM25 Index] Built index for {total_docs} chunks from Qdrant in {build_ms:.2f}ms.")

        # Save to disk cache
        try:
            self.bm25_index.save_to_disk(self.cache_path)
        except Exception as e:
            print(f"[BM25 Cache] Warning: could not persist BM25 cache: {e}")

    def rebuild_bm25_cache(self) -> None:
        """Forces rebuilding and saving the BM25 index cache."""
        self._build_bm25_index(force_rebuild=True)

    def retrieve(
        self,
        query: str,
        jurisdiction: str = "national",
        category: Optional[str] = None,
        dense_top_k: int = DENSE_TOP_K,
        bm25_top_k: int = BM25_TOP_K,
        rrf_k: int = RRF_K,
        fused_top_k: int = FUSED_TOP_K,
        rerank_top_k: int = RERANK_TOP_K,
        score_threshold: Optional[float] = None,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Executes the full hybrid legal retrieval pipeline.

        Returns:
            Tuple of (top_reranked_passages, diagnostic_metadata_dict).
        """
        j_clean = jurisdiction.lower().strip()

        # 1. Legal Query Normalization & Semantic Expansion
        norm_query, expanded_query = expand_legal_query(query)

        # 2. Dense Retrieval via BGE-M3 + Qdrant
        must_conditions = [
            FieldCondition(key="jurisdiction", match=MatchValue(value=j_clean))
        ]
        if category:
            must_conditions.append(
                FieldCondition(key="category", match=MatchValue(value=category))
            )
        query_filter = Filter(must=must_conditions)

        query_vector = self.embed_model.encode(
            expanded_query,
            normalize_embeddings=True,
            show_progress_bar=False,
        ).tolist()

        dense_response = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            query_filter=query_filter,
            limit=dense_top_k,
        )

        dense_hits = dense_response.points
        dense_candidates: Dict[str, Dict[str, Any]] = {}
        for rank, hit in enumerate(dense_hits, start=1):
            if hit.payload:
                doc_id = str(hit.id)
                p = dict(hit.payload)
                p["id"] = doc_id
                p["dense_rank"] = rank
                p["dense_score"] = float(hit.score)
                dense_candidates[doc_id] = p

        # 3. Sparse Retrieval via Legal BM25 Index
        bm25_norm_hits = self.bm25_index.search(
            query=norm_query,
            jurisdiction=j_clean,
            top_k=bm25_top_k,
        )
        bm25_candidates: Dict[str, Dict[str, Any]] = {}
        for hit in bm25_norm_hits:
            doc_id = str(hit.get("id"))
            bm25_candidates[doc_id] = hit

        # Also search expanded query in BM25 if different
        if norm_query != expanded_query:
            bm25_exp_hits = self.bm25_index.search(
                query=expanded_query,
                jurisdiction=j_clean,
                top_k=bm25_top_k,
            )
            for hit in bm25_exp_hits:
                doc_id = str(hit.get("id"))
                if doc_id not in bm25_candidates:
                    hit_copy = dict(hit)
                    hit_copy["bm25_rank"] = len(bm25_candidates) + 1
                    bm25_candidates[doc_id] = hit_copy

        # 4. Reciprocal Rank Fusion (RRF) & Deduplication
        all_doc_ids = set(dense_candidates.keys()).union(set(bm25_candidates.keys()))
        fused_pool: List[Dict[str, Any]] = []

        for doc_id in all_doc_ids:
            if doc_id in dense_candidates:
                candidate = dict(dense_candidates[doc_id])
            else:
                candidate = dict(bm25_candidates[doc_id])

            dense_r = dense_candidates.get(doc_id, {}).get("dense_rank")
            dense_s = dense_candidates.get(doc_id, {}).get("dense_score")
            bm25_r = bm25_candidates.get(doc_id, {}).get("bm25_rank")
            bm25_s = bm25_candidates.get(doc_id, {}).get("bm25_score")

            candidate["dense_rank"] = dense_r
            candidate["dense_score"] = dense_s
            candidate["bm25_rank"] = bm25_r
            candidate["bm25_score"] = bm25_s

            rrf_score = 0.0
            if dense_r is not None:
                rrf_score += 1.0 / (rrf_k + dense_r)
            if bm25_r is not None:
                rrf_score += 1.0 / (rrf_k + bm25_r)

            candidate["rrf_score"] = float(rrf_score)
            fused_pool.append(candidate)

        # Sort by RRF score descending
        fused_pool.sort(key=lambda x: x["rrf_score"], reverse=True)
        for rrf_idx, c in enumerate(fused_pool, start=1):
            c["rrf_rank"] = rrf_idx

        # Select top fused candidates
        selected_candidates = fused_pool[:fused_top_k]

        if not selected_candidates:
            diagnostics = {
                "query": query,
                "normalized_query": norm_query,
                "expanded_query": expanded_query,
                "dense_candidates_count": len(dense_candidates),
                "bm25_candidates_count": len(bm25_candidates),
                "unique_rrf_candidates_count": len(all_doc_ids),
                "passed_to_cross_encoder_count": 0,
                "final_top_k_count": 0,
            }
            return [], diagnostics

        # 5. Cross-Encoder Reranking
        # Format input text with statutory title and section citation for complete context
        pairs = []
        for c in selected_candidates:
            doc_context = f"{c.get('title', '')} {c.get('citation_prefix', '')} {c.get('section', '')}: {c.get('text', '')}"
            pairs.append([expanded_query, doc_context[:750]])

        with torch.inference_mode():
            raw_logits = self.rerank_model.predict(
                pairs,
                batch_size=self.batch_size,
                max_length=RERANK_MAX_LENGTH,
                show_progress_bar=False,
            )
        sigmoids = torch.sigmoid(torch.tensor(raw_logits, dtype=torch.float32)).tolist()

        for c, raw, sig in zip(selected_candidates, raw_logits, sigmoids):
            c["cross_encoder_raw_score"] = float(raw)
            c["score"] = float(raw)  # Raw logit used as ranking signal
            c["cross_encoder_sigmoid"] = float(sig)

        # Sort by CrossEncoder raw score descending
        reranked_pool = sorted(selected_candidates, key=lambda x: x["cross_encoder_raw_score"], reverse=True)
        for ce_idx, c in enumerate(reranked_pool, start=1):
            c["cross_encoder_rank"] = ce_idx

        # Document-diversified selection (max 3 passages per document title in final top-k to ensure cross-statute coverage without suppressing multiple key sections)
        diverse_top_k: List[Dict[str, Any]] = []
        doc_counts: Dict[str, int] = {}
        for c in reranked_pool:
            title = c.get("title", "")
            if doc_counts.get(title, 0) < 3:
                diverse_top_k.append(c)
                doc_counts[title] = doc_counts.get(title, 0) + 1
            if len(diverse_top_k) == rerank_top_k:
                break

        # If diversity didn't fill rerank_top_k, fill from remaining
        if len(diverse_top_k) < rerank_top_k:
            for c in reranked_pool:
                if c not in diverse_top_k:
                    diverse_top_k.append(c)
                if len(diverse_top_k) == rerank_top_k:
                    break

        diagnostics = {
            "query": query,
            "normalized_query": norm_query,
            "expanded_query": expanded_query,
            "dense_candidates_count": len(dense_candidates),
            "bm25_candidates_count": len(bm25_candidates),
            "unique_rrf_candidates_count": len(all_doc_ids),
            "passed_to_cross_encoder_count": len(selected_candidates),
            "final_top_k_count": len(diverse_top_k),
        }

        return diverse_top_k, diagnostics


# Singleton retriever instance
_default_retriever: Optional[LegalRetriever] = None


def get_default_retriever() -> LegalRetriever:
    global _default_retriever
    if _default_retriever is None:
        _default_retriever = LegalRetriever()
    return _default_retriever


def retrieve(
    query: str,
    jurisdiction: str = "national",
    category: Optional[str] = None,
    dense_top_k: int = DENSE_TOP_K,
    bm25_top_k: int = BM25_TOP_K,
    rrf_k: int = RRF_K,
    fused_top_k: int = FUSED_TOP_K,
    rerank_top_k: int = RERANK_TOP_K,
    max_per_doc: int = 3,
) -> Dict[str, Any]:
    """Module-level retrieve wrapper returning results, raw_candidates, and diagnostics."""
    retriever = get_default_retriever()
    top_results, diagnostics = retriever.retrieve(
        query=query,
        jurisdiction=jurisdiction,
        category=category,
        dense_top_k=dense_top_k,
        bm25_top_k=bm25_top_k,
        rrf_k=rrf_k,
        fused_top_k=fused_top_k,
        rerank_top_k=rerank_top_k,
    )
    return {
        "results": top_results,
        "raw_candidates": top_results,
        "diagnostics": diagnostics,
    }
