import time
import requests
import json
import sys

if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

BASE_URL = "http://127.0.0.1:8000"

def test_streaming_query(query_text: str, jurisdiction: str = "national"):
    print("=" * 80)
    print(f"QUERY: \"{query_text}\" (Jurisdiction: {jurisdiction})")
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
    events = []
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
                events.append(ev)
                if ev.get("stage") == "complete":
                    final_data = ev.get("data", {})
            except Exception:
                pass
                
    total_elapsed = (time.perf_counter() - t0) * 1000
    
    print(f"Time to First Event (TTFE) : {first_event_time:6.1f} ms")
    print(f"Total Stream Duration      : {total_elapsed:6.1f} ms ({total_elapsed/1000:.2f}s)")
    if final_data:
        timing = final_data.get("timing_ms", {})
        print(f"Server Timing Breakdown    : Retrieval: {timing.get('retrieval')}ms | LLM: {timing.get('llm')}ms | Total: {timing.get('total')}ms")
        print(f"Provider Used              : {final_data.get('provider_used')}")
        print(f"Confidence                 : {final_data.get('confidence')}")
        print(f"Citations ({len(final_data.get('citations', []))}):")
        for c in final_data.get("citations", []):
            print(f"  - [{c.get('source')}] {c.get('section')}")
        print("\nAnswer Excerpt:")
        ans = final_data.get("answer", "")
        print(ans[:300] + ("..." if len(ans) > 300 else ""))
    print("=" * 80 + "\n")
    return total_elapsed

def main():
    queries = [
        ("What are the labelling requirements for Ayurvedic drugs under Rule 161?", "national"),
        ("What constitutes an authorized user of a registered Geographical Indication under Section 8 of the GI Act?", "national"),
        ("Can authentic regional origin for herbal and agricultural crops be protected as a Geographical Indication?", "national"),
        ("Can a novel, structurally modified synthetic derivative of a chemical compound found in an Ayurvedic plant be patented in India?", "national"),
    ]
    
    durations = []
    for q, jur in queries:
        dur = test_streaming_query(q, jur)
        durations.append(dur)
        time.sleep(0.5)
        
    print("=" * 80)
    print(f"AVERAGE LIVE END-TO-END STREAMING LATENCY: {sum(durations)/len(durations):.1f} ms ({sum(durations)/len(durations)/1000:.2f}s)")
    print("=" * 80)

if __name__ == "__main__":
    main()
