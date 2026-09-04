# -*- coding: utf-8 -*-
import requests
import json

BASE_URL = "http://localhost:8000"

POS_QUERY = "Can someone else patent my grandmother's classical Ayurvedic formulation?"
NEG_QUERY_1 = "What are the labelling requirements under Rule 161?"
NEG_QUERY_2 = "How do I register a trademark?"

def run_tests():
    print("=== 1. Testing /compliance/case-study endpoint ===")
    
    # 1. Positive trigger
    r_pos = requests.post(f"{BASE_URL}/compliance/case-study", json={"query": POS_QUERY})
    assert r_pos.status_code == 200, f"Expected 200, got {r_pos.status_code}"
    pos_data = r_pos.json()
    assert pos_data.get("triggered") is True, f"Expected triggered=True for: {POS_QUERY}"
    assert "turmeric_case" in pos_data, "Missing turmeric_case in payload"
    assert "neem_case" in pos_data, "Missing neem_case in payload"
    assert "closing_line" in pos_data, "Missing closing_line in payload"
    assert "source_footnote" in pos_data, "Missing source_footnote in payload"
    
    print("[PASS] Positive query triggered case-study card successfully:")
    print("  Title:", pos_data.get("title"))
    print("  Turmeric:", pos_data["turmeric_case"]["title"])
    print("  Neem:", pos_data["neem_case"]["title"])
    print("  Footnote:", pos_data["source_footnote"])

    # 2. Negative queries
    r_neg1 = requests.post(f"{BASE_URL}/compliance/case-study", json={"query": NEG_QUERY_1})
    assert r_neg1.status_code == 200
    neg1_data = r_neg1.json()
    assert neg1_data.get("triggered") is False, f"Expected triggered=False for: {NEG_QUERY_1}"
    print(f"[PASS] Negative query 1 rejected successfully: '{NEG_QUERY_1}' -> triggered={neg1_data.get('triggered')}")

    r_neg2 = requests.post(f"{BASE_URL}/compliance/case-study", json={"query": NEG_QUERY_2})
    assert r_neg2.status_code == 200
    neg2_data = r_neg2.json()
    assert neg2_data.get("triggered") is False, f"Expected triggered=False for: {NEG_QUERY_2}"
    print(f"[PASS] Negative query 2 rejected successfully: '{NEG_QUERY_2}' -> triggered={neg2_data.get('triggered')}")

    print("\n=== 2. Testing /compliance/tkdl endpoint ===")
    r_tkdl = requests.post(f"{BASE_URL}/compliance/tkdl", json={"query": POS_QUERY})
    tkdl_data = r_tkdl.json()
    assert tkdl_data.get("triggered") is True
    assert "case_study" in tkdl_data and tkdl_data["case_study"]["triggered"] is True
    print("[PASS] /compliance/tkdl embeds case_study successfully.")

    print("\n=== 3. Testing /ask endpoint ===")
    r_ask_pos = requests.post(f"{BASE_URL}/ask", json={"query": POS_QUERY, "jurisdiction": "national"})
    ask_pos_data = r_ask_pos.json()
    assert ask_pos_data.get("case_study") is not None and ask_pos_data["case_study"]["triggered"] is True
    print("[PASS] /ask includes case_study for positive query.")

    r_ask_neg = requests.post(f"{BASE_URL}/ask", json={"query": NEG_QUERY_1, "jurisdiction": "national"})
    ask_neg_data = r_ask_neg.json()
    assert ask_neg_data.get("case_study") is None or ask_neg_data["case_study"].get("triggered") is False
    print("[PASS] /ask omits case_study for labelling query.")

    print("\n>>> ALL TESTS PASSED SUCCESSFULLY! <<<")

if __name__ == "__main__":
    run_tests()
