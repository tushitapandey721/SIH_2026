import time
import requests
import json
import sys

if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

BASE_URL = "http://127.0.0.1:8000"

def run_rapid_fire_query(idx: int, query_text: str, jurisdiction: str = "national"):
    print("=" * 80)
    print(f"QUERY [{idx}/6]: \"{query_text}\" (Jurisdiction: {jurisdiction})")
    print("=" * 80)
    
    payload = {
        "query": query_text,
        "jurisdiction": jurisdiction,
        "formulation_answers": {},
        "conversation_id": None,
    }
    
    t0 = time.perf_counter()
    response = requests.post(f"{BASE_URL}/ask/stream", json=payload, stream=True)
    
    first_event_time = None
    final_data = None
    
    for line in response.iter_lines():
        if not line:
            continue
        line_str = line.decode("utf-8")
        if first_event_time is None:
            first_event_time = (time.perf_counter() - t0) * 1000
            
        if line_str.startswith("data: "):
            try:
                ev = json.loads(line_str[6:])
                if ev.get("stage") == "complete":
                    final_data = ev.get("data", {})
            except Exception:
                pass
                
    total_elapsed = (time.perf_counter() - t0) * 1000
    
    provider = final_data.get("provider_used", "unknown") if final_data else "none"
    timing = final_data.get("timing_ms", {}) if final_data else {}
    ret_ms = timing.get("retrieval", 0)
    llm_ms = timing.get("llm", 0)
    
    print(f"Result for Query [{idx}]:")
    print(f"  - Provider Used    : {provider.upper()}")
    print(f"  - Time to 1st Byte : {first_event_time:.1f} ms" if first_event_time else "  - Time to 1st Byte : N/A")
    print(f"  - Retrieval Time   : {ret_ms:.1f} ms")
    print(f"  - LLM Gen Time     : {llm_ms:.1f} ms ({llm_ms/1000:.2f}s)")
    print(f"  - Total Latency    : {total_elapsed:.1f} ms ({total_elapsed/1000:.2f}s)")
    print(f"  - Citations        : {[c.get('section') for c in final_data.get('citations', [])] if final_data else []}")
    print("=" * 80 + "\n")
    return {
        "idx": idx,
        "query": query_text,
        "provider": provider,
        "ret_ms": ret_ms,
        "llm_ms": llm_ms,
        "total_ms": total_elapsed,
    }

def main():
    test_queries = [
        ("What does Section 3(p) of the Patents Act prohibit?", "national"),
        ("What are the labelling requirements for Ayurvedic drugs under Rule 161?", "national"),
        ("What constitutes an authorized user of a registered Geographical Indication under Section 8 of the GI Act?", "national"),
        ("Can authentic regional origin for herbal and agricultural crops be protected as a Geographical Indication?", "national"),
        ("Can a novel, structurally modified synthetic derivative of a chemical compound found in an Ayurvedic plant be patented in India?", "national"),
        ("What is the legal difference between a classical Ayurvedic medicine and a proprietary ASU formulation under Rule 158B?", "national"),
    ]
    
    print("STARTING RAPID-FIRE MULTI-QUERY TEST (6 queries back-to-back with 0 delay)...\n")
    t_start = time.perf_counter()
    results = []
    
    for i, (q, jur) in enumerate(test_queries, 1):
        res = run_rapid_fire_query(i, q, jur)
        results.append(res)
        # zero delay between queries to deliberately saturate free-tier TPM
        
    t_total = time.perf_counter() - t_start
    print("=" * 80)
    print(f"RAPID-FIRE TEST SUMMARY (Total Elapsed: {t_total:.2f}s for 6 queries)")
    print("=" * 80)
    print(f"{'#':<3} | {'Provider':<8} | {'Retrieval':<10} | {'LLM Time':<10} | {'Total Latency':<12} | {'Query Snippet'}")
    print("-" * 80)
    for r in results:
        print(f"{r['idx']:<3} | {r['provider'].upper():<8} | {r['ret_ms']:<8.1f}ms | {r['llm_ms']:<8.1f}ms | {r['total_ms']:<10.1f}ms | {r['query'][:35]}...")
    print("=" * 80)

if __name__ == "__main__":
    main()
