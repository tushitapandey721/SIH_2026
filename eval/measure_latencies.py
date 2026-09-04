import time
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.retrieval.retrieve import LegalRetriever

def main():
    print("=" * 80)
    print("WARM-STATE RETRIEVAL LATENCY MEASUREMENT (FP16 CUDA)")
    print("=" * 80)
    
    retriever = LegalRetriever()
    
    # 1. Warmup query to ensure CUDA kernels, PyTorch JIT, and model weights are hot
    print("Running warmup query...")
    retriever.retrieve("What does Section 3(p) of the Patents Act prohibit?", jurisdiction="national")
    
    test_queries = [
        ("Q09", "What are the labelling requirements for Ayurvedic drugs under Rule 161?", "national"),
        ("Q27", "What constitutes an authorized user of a registered Geographical Indication under Section 8 of the GI Act?", "national"),
        ("Q30", "Can authentic regional origin for herbal and agricultural crops be protected as a Geographical Indication?", "national"),
        ("Q31", "Can a novel, structurally modified synthetic derivative of a chemical compound found in an Ayurvedic plant be patented in India?", "national"),
        ("Q21", "What is an inventive step under the Patents Act?", "national"),
        ("Q17", "What is patentable subject matter under TRIPS Article 27?", "international"),
        ("Q16", "What does Article 6 of the Nagoya Protocol cover?", "international"),
        ("Q24", "What qualifies as a new invention under the Patents Act?", "national"),
    ]
    
    latencies = []
    for q_id, q_text, jur in test_queries:
        t0 = time.perf_counter()
        results, diag = retriever.retrieve(q_text, jurisdiction=jur)
        lat = (time.perf_counter() - t0) * 1000
        latencies.append(lat)
        top1 = results[0] if results else {}
        print(f"[{q_id}] Latency: {lat:6.1f} ms | Top-1: [{top1.get('title')}] {top1.get('section')}")
        
    avg_lat = sum(latencies) / len(latencies)
    min_lat = min(latencies)
    max_lat = max(latencies)
    print("=" * 80)
    print(f"Average Warm Retrieval Latency : {avg_lat:6.1f} ms")
    print(f"Min Retrieval Latency          : {min_lat:6.1f} ms")
    print(f"Max Retrieval Latency          : {max_lat:6.1f} ms")
    print("=" * 80)

if __name__ == "__main__":
    main()
