import time
import requests
import json
import sys

if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

BASE_URL = "http://127.0.0.1:8000"

def query_stream(query: str, jurisdiction: str = "national", history = None):
    payload = {
        "query": query,
        "jurisdiction": jurisdiction,
        "formulation_answers": {},
        "conversation_id": None,
        "history": history or []
    }
    
    t0 = time.perf_counter()
    resp = requests.post(f"{BASE_URL}/ask/stream", json=payload, stream=True)
    
    final_payload = None
    stages = []
    
    for line in resp.iter_lines():
        if not line:
            continue
        line_str = line.decode("utf-8")
        if line_str.startswith("data: "):
            try:
                ev = json.loads(line_str[6:])
                if ev.get("stage"):
                    stages.append(ev.get("stage"))
                if ev.get("stage") == "complete":
                    final_payload = ev.get("data")
            except Exception:
                pass
                
    elapsed = (time.perf_counter() - t0) * 1000
    return final_payload, stages, elapsed

def main():
    print("=" * 80)
    print("TESTING CONVERSATIONAL TRANSLATION & MULTI-TURN CONTEXT")
    print("=" * 80)
    
    # Step 1: Initial query in Hindi
    q1 = "क्या मैं पारंपरिक ज्ञान का पेटेंट करा सकता हूँ?"
    print(f"\n[Step 1] User asks in Hindi: \"{q1}\"")
    res1, stages1, time1 = query_stream(q1, jurisdiction="national", history=[])
    print(f"  Latency: {time1:.1f}ms | Detected Lang: {res1.get('language')}")
    print(f"  Hindi Answer: {res1.get('answer')[:120]}...")
    print(f"  Citations: {res1.get('citations')}")
    print(f"  Abstained: {res1.get('abstained')}")
    
    history = [
        {"role": "user", "content": q1, "citations": []},
        {"role": "assistant", "content": res1.get("answer"), "citations": res1.get("citations"), "language": res1.get("language")}
    ]
    
    # Step 2: Follow-up query asking to convert above response to English
    q2 = "convert the above response to english"
    print(f"\n[Step 2] User asks follow-up: \"{q2}\"")
    res2, stages2, time2 = query_stream(q2, jurisdiction="national", history=history)
    print(f"  Latency: {time2:.1f}ms | Lang: {res2.get('language')}")
    print(f"  Classification: {res2.get('classification')}")
    print(f"  English Answer: {res2.get('answer')}")
    print(f"  Citations Preserved: {res2.get('citations')}")
    print(f"  Abstained: {res2.get('abstained')}")
    
    # Step 3: Follow-up query asking to translate in Hindi again
    history.extend([
        {"role": "user", "content": q2, "citations": []},
        {"role": "assistant", "content": res2.get("answer"), "citations": res2.get("citations"), "language": res2.get("language")}
    ])
    
    q3 = "translate the above to hindi"
    print(f"\n[Step 3] User asks follow-up: \"{q3}\"")
    res3, stages3, time3 = query_stream(q3, jurisdiction="national", history=history)
    print(f"  Latency: {time3:.1f}ms | Lang: {res3.get('language')}")
    print(f"  Hindi Answer: {res3.get('answer')}")
    print(f"  Citations Preserved: {res3.get('citations')}")
    print(f"  Abstained: {res3.get('abstained')}")

if __name__ == "__main__":
    main()
