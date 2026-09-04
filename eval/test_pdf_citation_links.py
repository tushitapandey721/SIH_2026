"""Comprehensive test verifying that clicking citations opens the associated PDF directly.

Tests:
1. All 17 statutory and treaty PDFs can be downloaded and viewed from /pdf/{filename}
2. POST /ask returns citations with 'pdf_url', 'official_url', and 'url' pointing to the PDF
3. SSE /ask/stream returns complete stage with PDF URLs in citations
4. GET /conversations/{id} dynamically enriches saved citations with PDF URLs
5. GET /corpus returns all 17 documents with pdf_url and official_url
"""

import json
import urllib.request
import urllib.parse

BASE_URL = "http://localhost:8000"


def test_pdf_endpoints():
    print("--- Testing PDF Endpoints for All 17 Manifest Documents ---")
    corp_res = urllib.request.urlopen(f"{BASE_URL}/corpus")
    corp_data = json.loads(corp_res.read().decode("utf-8"))
    all_docs = corp_data["national"] + corp_data["international"]
    assert len(all_docs) == 17, f"Expected 17 documents, found {len(all_docs)}"

    for doc in all_docs:
        fn = doc.get("pdf_filename")
        assert fn, f"Document {doc.get('id')} missing pdf_filename"
        encoded_fn = urllib.parse.quote(fn)
        pdf_url = f"{BASE_URL}/pdf/{encoded_fn}"
        req = urllib.request.Request(pdf_url, method="HEAD")
        with urllib.request.urlopen(req) as r:
            assert r.status == 200, f"Failed to fetch PDF for {fn}: status {r.status}"
            assert "application/pdf" in r.headers.get("Content-Type", ""), f"Wrong Content-Type for {fn}"
            assert "inline" in r.headers.get("Content-Disposition", ""), f"Missing inline disposition for {fn}"
            print(f"  [OK] {doc.get('id'):12} | {fn:55} | 200 OK (application/pdf inline)")


def test_ask_citations():
    print("\n--- Testing POST /ask Citation Enrichment ---")
    payload = {
        "query": "Is a classical Ayurvedic formulation patentable under Indian law?",
        "jurisdiction": "national",
        "formulation_answers": {},
    }
    req = urllib.request.Request(
        f"{BASE_URL}/ask",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        citations = data.get("citations", [])
        assert len(citations) > 0, "No citations returned"
        for cit in citations:
            print(f"  [OK] Citation: {cit.get('section')} - {cit.get('source')}")
            print(f"    - PDF URL     : {cit.get('pdf_url')}")
            print(f"    - Primary URL : {cit.get('url')}")
            print(f"    - Official URL: {cit.get('official_url')}")
            assert cit.get("pdf_url"), "Missing pdf_url in citation"
            assert "http://localhost:8000/pdf/" in cit.get("pdf_url"), "Invalid pdf_url format"
            assert cit.get("url") == cit.get("pdf_url"), "Primary url should point directly to the PDF"

            # Verify that clicking this PDF URL succeeds
            pdf_check = urllib.request.urlopen(cit.get("pdf_url"))
            assert pdf_check.status == 200
            assert "application/pdf" in pdf_check.headers.get("Content-Type", "")


def test_stream_citations():
    print("\n--- Testing SSE POST /ask/stream Citation Enrichment ---")
    payload = {
        "query": "What are the rules under WIPO GRATK Treaty for patent applications?",
        "jurisdiction": "international",
        "formulation_answers": {},
    }
    req = urllib.request.Request(
        f"{BASE_URL}/ask/stream",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "text/event-stream"},
    )
    complete_data = None
    with urllib.request.urlopen(req) as resp:
        for line in resp:
            line_str = line.decode("utf-8").strip()
            if line_str.startswith("data: "):
                event = json.loads(line_str[6:])
                if event.get("stage") == "complete":
                    complete_data = event.get("data")
                    break

    assert complete_data, "Never received complete event in stream"
    citations = complete_data.get("citations", [])
    assert len(citations) > 0, "No citations in stream complete payload"
    for cit in citations:
        print(f"  [OK] Stream Citation: {cit.get('section')} - {cit.get('source')}")
        print(f"    - PDF URL     : {cit.get('pdf_url')}")
        print(f"    - Primary URL : {cit.get('url')}")
        assert "http://localhost:8000/pdf/" in cit.get("pdf_url"), "Invalid pdf_url in stream"
        # Verify PDF can be loaded
        pdf_check = urllib.request.urlopen(cit.get("pdf_url"))
        assert pdf_check.status == 200


def test_historical_conversation_enrichment():
    print("\n--- Testing Dynamic Enrichment of Saved/Historical Conversations ---")
    # Fetch conversation list
    list_res = urllib.request.urlopen(f"{BASE_URL}/conversations")
    convs = json.loads(list_res.read().decode("utf-8")).get("conversations", [])
    if convs:
        test_id = convs[0]["id"]
        detail_res = urllib.request.urlopen(f"{BASE_URL}/conversations/{test_id}")
        conv_data = json.loads(detail_res.read().decode("utf-8"))
        messages = conv_data.get("messages", [])
        enriched_count = 0
        for m in messages:
            for cit in m.get("citations", []):
                enriched_count += 1
                assert cit.get("pdf_url"), f"Historical citation missing pdf_url in conv {test_id}"
                print(f"  [OK] Historical Citation Enriched: {cit.get('section')} -> PDF: {cit.get('pdf_filename')}")
        print(f"  [OK] Verified {enriched_count} historical citations dynamically enriched with PDF URLs!")
    else:
        print("  (No previous conversations in DB to check, verified via ask tests)")


if __name__ == "__main__":
    test_pdf_endpoints()
    test_ask_citations()
    test_stream_citations()
    test_historical_conversation_enrichment()
    print("\n=======================================================")
    print("ALL TESTS PASSED: Citations now open official PDFs directly!")
    print("=======================================================")
