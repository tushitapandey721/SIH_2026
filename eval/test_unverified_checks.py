import time
import requests
import json
import sys

if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

BASE_URL = "http://127.0.0.1:8000"

def query_stream_endpoint(query: str, jurisdiction: str = "national"):
    payload = {
        "query": query,
        "jurisdiction": jurisdiction,
        "formulation_answers": {},
        "conversation_id": None,
    }
    
    t0 = time.perf_counter()
    resp = requests.post(f"{BASE_URL}/ask/stream", json=payload, stream=True)
    
    final_payload = None
    stream_events = []
    
    for line in resp.iter_lines():
        if not line:
            continue
        line_str = line.decode("utf-8")
        if line_str.startswith("data: "):
            try:
                ev = json.loads(line_str[6:])
                stream_events.append(ev)
                if ev.get("stage") == "complete":
                    final_payload = ev.get("data")
            except Exception:
                pass
                
    elapsed = (time.perf_counter() - t0) * 1000
    return final_payload, elapsed

def main():
    print("=" * 90)
    print("TEST 1: JURISDICTION SEPARATION VERIFICATION")
    print("=" * 90)
    
    q_tk = "Can I patent traditional knowledge?"
    
    # 1a. National
    print(f"\n--- [1a] Querying National Jurisdiction: \"{q_tk}\" ---")
    res_nat, time_nat = query_stream_endpoint(q_tk, jurisdiction="national")
    print(f"Latency: {time_nat:.1f} ms")
    print("Full Raw Response JSON (National):")
    print(json.dumps(res_nat, indent=2, ensure_ascii=False))
    
    time.sleep(1)
    
    # 1b. International
    print(f"\n--- [1b] Querying International Jurisdiction: \"{q_tk}\" ---")
    res_intl, time_intl = query_stream_endpoint(q_tk, jurisdiction="international")
    print(f"Latency: {time_intl:.1f} ms")
    print("Full Raw Response JSON (International):")
    print(json.dumps(res_intl, indent=2, ensure_ascii=False))
    
    time.sleep(1)
    
    print("\n" + "=" * 90)
    print("TEST 2: ABSTENTION ON OUT-OF-SCOPE INQUIRY")
    print("=" * 90)
    
    q_out = "What is the trademark registration fee in Japan?"
    print(f"\n--- [2] Querying Out-Of-Scope: \"{q_out}\" ---")
    res_abs, time_abs = query_stream_endpoint(q_out, jurisdiction="national")
    print(f"Latency: {time_abs:.1f} ms")
    print("Full Raw Response JSON (Out-of-Scope):")
    print(json.dumps(res_abs, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
