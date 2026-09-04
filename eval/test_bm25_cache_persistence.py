"""Automated test for BM25 disk cache serialization, deserialization, and speedup."""

import sys
import time
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.retrieval.bm25 import BM25Index
from app.retrieval.retrieve import get_default_retriever


def test_bm25_cache():
    print("=" * 80)
    print("TEST: BM25 Disk Cache Persistence & Parity")
    print("=" * 80)

    retriever = get_default_retriever()
    cache_file = retriever.cache_path

    print(f"Target BM25 cache file: {cache_file}")

    # 1. Force rebuild and save
    t_rebuild_start = time.perf_counter()
    retriever.rebuild_bm25_cache()
    rebuild_ms = (time.perf_counter() - t_rebuild_start) * 1000
    print(f"1. Force rebuild completed in {rebuild_ms:.2f}ms")

    assert cache_file.exists(), f"Cache file {cache_file} was not created!"
    file_size_kb = cache_file.stat().st_size / 1024
    print(f"   Cache file exists! Compressed file size: {file_size_kb:.2f} KB")

    # 2. Search before loading cache to record baseline scores
    sample_query = "Section 3(p) traditional knowledge not patentable"
    hits_fresh = retriever.bm25_index.search(sample_query, jurisdiction="national", top_k=5)
    print(f"2. Sample query top-1: {hits_fresh[0].get('section')} (score: {hits_fresh[0].get('bm25_score'):.4f})")

    # 3. Test direct load_from_disk
    t_load_start = time.perf_counter()
    loaded_index = BM25Index.load_from_disk(cache_file)
    load_ms = (time.perf_counter() - t_load_start) * 1000
    print(f"3. Direct BM25Index.load_from_disk completed in {load_ms:.2f}ms")

    # 4. Search on loaded index and verify exact parity
    hits_cached = loaded_index.search(sample_query, jurisdiction="national", top_k=5)
    print(f"4. Cached query top-1: {hits_cached[0].get('section')} (score: {hits_cached[0].get('bm25_score'):.4f})")

    assert len(hits_fresh) == len(hits_cached), "Hit counts do not match!"
    for idx in range(len(hits_fresh)):
        assert hits_fresh[idx]["id"] == hits_cached[idx]["id"], f"Rank {idx+1} doc ID mismatch!"
        assert abs(hits_fresh[idx]["bm25_score"] - hits_cached[idx]["bm25_score"]) < 1e-5, f"Score mismatch at rank {idx+1}"

    print("   [PARITY CHECK] 100% exact parity verified across all retrieved hits!")
    print(f"   [SPEEDUP] Rebuild: {rebuild_ms:.2f}ms -> Cache Load: {load_ms:.2f}ms ({rebuild_ms / max(load_ms, 0.01):.1f}x faster startup)")
    print("=" * 80)
    print("BM25 CACHE PERSISTENCE TEST PASSED! SUCCESS!")
    print("=" * 80)


if __name__ == "__main__":
    test_bm25_cache()
