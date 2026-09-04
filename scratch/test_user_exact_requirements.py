import requests
import json
from app.compliance.tkdl_helper import detect_tkdl_trigger, build_tkdl_pointer_payload

test_cases = [
    ("Can someone else patent my grandmother's classical Ayurvedic oil recipe?", True),
    ("What are the labelling requirements under Rule 161?", False),
    ("How do I register a trademark?", False),
]

print("=== 1. Direct Unit Tests on detect_tkdl_trigger & payload ===")
for q, expected in test_cases:
    # Test with classification="classical_medicine"
    trig_classical = detect_tkdl_trigger(q, classification="classical_medicine")
    # Test with classification=None
    trig_none = detect_tkdl_trigger(q, classification=None)
    payload = build_tkdl_pointer_payload(q, classification="classical_medicine" if expected else None)
    
    print(f"Query: '{q}'")
    print(f"  trig (class=classical_medicine): {trig_classical}")
    print(f"  trig (class=None): {trig_none}")
    print(f"  payload triggered: {payload.get('triggered')} (Expected: {expected})")
    
    assert (trig_classical and trig_none) == expected if expected else (trig_classical == False and trig_none == False), \
        f"Unit test failed for '{q}'"

print("\n=== 2. API Test on /compliance/tkdl ===")
for q, expected in test_cases:
    res = requests.post("http://127.0.0.1:8000/compliance/tkdl", json={"query": q}, timeout=10)
    data = res.json()
    print(f"API Query: '{q}' -> Triggered: {data.get('triggered')} (Expected: {expected})")
    assert data.get("triggered") == expected, f"API test failed for '{q}'"

print("\n=== 3. API Test on /ask/stream (Full pipeline event stream) ===")
import json

for q, expected in test_cases:
    res = requests.post("http://127.0.0.1:8000/ask/stream", json={"query": q, "jurisdiction": "national"}, stream=True, timeout=15)
    tkdl_event = None
    complete_tkdl = None
    for line in res.iter_lines():
        if line:
            line_str = line.decode('utf-8')
            if line_str.startswith("data: "):
                event_data = json.loads(line_str[6:])
                if event_data.get("stage") == "tkdl_pointer":
                    tkdl_event = event_data.get("data")
                if event_data.get("stage") == "complete":
                    complete_tkdl = event_data.get("data", {}).get("tkdl_pointer")
    
    print(f"Stream Query: '{q}'")
    is_trig = False
    if tkdl_event and tkdl_event.get("triggered"):
        is_trig = True
    elif complete_tkdl and complete_tkdl.get("triggered"):
        is_trig = True
        
    print(f"  Stream TKDL triggered: {is_trig} (Expected: {expected})")
    assert is_trig == expected, f"Stream mismatch for '{q}': got {is_trig}, expected {expected}"

print("\n>>> ALL EXACT USER TESTS PASSED PERFECTLY! <<<")
