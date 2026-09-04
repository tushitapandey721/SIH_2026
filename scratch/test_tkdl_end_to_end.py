"""End-to-end test script for TKDL Prior-Art Pointer integration."""
import json
import requests

BASE_URL = "http://127.0.0.1:8000"

print("--- 1. Testing POST /compliance/tkdl direct endpoint ---")
tkdl_req_payload = {
    "query": "My grandmother gave me a traditional recipe for a joint pain oil made from classical Ayurvedic texts — can I patent it?",
    "classification": None,
}
res = requests.post(f"{BASE_URL}/compliance/tkdl", json=tkdl_req_payload, timeout=10)
print(f"Status Code: {res.status_code}")
assert res.status_code == 200, f"Expected 200, got {res.status_code}"
tkdl_data = res.json()
print("TKDL Direct Response Title:", tkdl_data.get("title"))
print("Statutory Provision:", tkdl_data.get("statutory_provision"))
print("Official URL:", tkdl_data.get("official_portal_url"))
print("Kalpana Category:", tkdl_data.get("hints", {}).get("formulation_category"))
print("Therapeutic Indication:", tkdl_data.get("hints", {}).get("therapeutic_area"))
print("IPC Classes:", [c["code"] for c in tkdl_data.get("hints", {}).get("ipc_classes", [])])
print("Source Texts Count:", len(tkdl_data.get("hints", {}).get("classical_source_texts", [])))
print("Workflow Steps Count:", len(tkdl_data.get("patent_examiner_workflow", [])))

assert tkdl_data["triggered"] is True
assert "Taila Kalpana" in tkdl_data["hints"]["formulation_category"]
assert "Sandhivata" in tkdl_data["hints"]["therapeutic_area"]
assert any(ipc["code"] == "A61K 36/00" for ipc in tkdl_data["hints"]["ipc_classes"])
assert tkdl_data["official_portal_url"] == "https://www.tkdl.res.in"
assert tkdl_data["hints"]["is_simulated_search"] is False
print(">>> TEST 1 PASSED!\n")

print("--- 2. Testing POST /ask with Grandmother Oil Recipe ---")
ask_payload = {
    "query": "My grandmother gave me a family recipe for a herbal joint pain oil made from classical Ayurvedic texts — can I patent it?",
    "jurisdiction": "national",
    "formulation_answers": {},
    "history": [],
}
res_ask = requests.post(f"{BASE_URL}/ask", json=ask_payload, timeout=30)
print(f"Status Code: {res_ask.status_code}")
assert res_ask.status_code == 200, f"Expected 200, got {res_ask.status_code}"
ask_data = res_ask.json()
print("Answer Snippet:", ask_data.get("answer", "")[:180], "...")
print("Citations Found:", len(ask_data.get("citations", [])))
for c in ask_data.get("citations", [])[:3]:
    print(f" - {c.get('source')} | Section {c.get('section')}")
print("Has tkdl_pointer:", "tkdl_pointer" in ask_data and ask_data["tkdl_pointer"] is not None)
if ask_data.get("tkdl_pointer"):
    print("tkdl_pointer Title:", ask_data["tkdl_pointer"]["title"])
    print("tkdl_pointer Category:", ask_data["tkdl_pointer"]["hints"]["formulation_category"])
assert ask_data.get("tkdl_pointer") is not None
assert ask_data["tkdl_pointer"]["triggered"] is True
assert "Taila Kalpana" in ask_data["tkdl_pointer"]["hints"]["formulation_category"]
print(">>> TEST 2 PASSED!\n")

print("--- 3. Testing POST /ask/stream SSE Events ---")
res_stream = requests.post(f"{BASE_URL}/ask/stream", json=ask_payload, stream=True, timeout=30)
print(f"Status Code: {res_stream.status_code}")
assert res_stream.status_code == 200, f"Expected 200, got {res_stream.status_code}"

stages_seen = []
tkdl_stage_data = None
complete_stage_data = None

for line in res_stream.iter_lines():
    if not line:
        continue
    line_str = line.decode("utf-8")
    if line_str.startswith("data: "):
        event = json.loads(line_str[6:])
        stage = event.get("stage")
        if stage and stage not in stages_seen:
            stages_seen.append(stage)
        if stage == "tkdl_pointer":
            tkdl_stage_data = event.get("data")
        elif stage == "complete":
            complete_stage_data = event.get("data")

print("Stages Seen in SSE Stream:", stages_seen)
assert "tkdl_pointer" in stages_seen, "Expected 'tkdl_pointer' stage in SSE stream!"
assert tkdl_stage_data is not None
assert tkdl_stage_data["triggered"] is True
print("tkdl_pointer Stage Verified:", tkdl_stage_data["hints"]["formulation_category"])

assert complete_stage_data is not None
assert complete_stage_data.get("tkdl_pointer") is not None
print("complete Stage Verified (has tkdl_pointer):", complete_stage_data["tkdl_pointer"]["hints"]["formulation_category"])
print(">>> TEST 3 PASSED!\n")

print("--- 4. Testing Negative Trigger (Non-Classical, Non-Patent Query) ---")
negative_payload = {
    "query": "What are the Madrid Protocol filing fees in India for trademark classes 35 and 42?",
    "jurisdiction": "international",
    "formulation_answers": {},
    "history": [],
}
res_neg = requests.post(f"{BASE_URL}/ask", json=negative_payload, timeout=30)
assert res_neg.status_code == 200
neg_data = res_neg.json()
print("Negative Query Has tkdl_pointer:", neg_data.get("tkdl_pointer") is not None)
assert neg_data.get("tkdl_pointer") is None
print(">>> TEST 4 PASSED!\n")

print("==================================================")
print("ALL END-TO-END TKDL TESTS COMPLETED SUCCESSFULLY!")
print("==================================================")
