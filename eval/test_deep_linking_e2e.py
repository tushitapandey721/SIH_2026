import sys
import os

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import requests
import json
import urllib.parse

BASE_URL = "http://127.0.0.1:8000"

test_queries = [
    {
        "query": "What are the patent exclusions under Section 3(p) and Section 3(d) of the Patents Act, 1970 regarding traditional knowledge?",
        "jurisdiction": "national",
    },
    {
        "query": "What are the requirements for ASU drugs manufacturing license under Rule 158-B of Drugs and Cosmetics Rules, 1945?",
        "jurisdiction": "national",
    },
    {
        "query": "Explain Section 3 and Section 6 approval requirements from National Biodiversity Authority under Biological Diversity Act and Rule 14 of BD Rules 2024.",
        "jurisdiction": "national",
    },
    {
        "query": "How do TRIPS Article 27, Nagoya Protocol Article 15, and WIPO GRATK Treaty Article 3 mandate patent disclosure of genetic resources?",
        "jurisdiction": "international",
    }
]

def run_tests():
    print("=" * 75)
    print("1. TESTING PDF STATIC ENDPOINTS AND STREAMING HEADERS")
    print("=" * 75)
    
    pdf_names = [
        "Patents Act, 1970.pdf",
        "Drugs and Cosmetics Rules, 1945.pdf",
        "Biological Diversity Act, 2002.pdf",
        "Biological Diversity Rules, 2024.pdf",
        "TRIPS Agreement (1994).pdf",
        "Nagoya Protocol (2010).pdf",
        "WIPO GRATK Treaty (2024).pdf"
    ]
    
    all_pdfs_ok = True
    for name in pdf_names:
        encoded_name = urllib.parse.quote(name)
        url = f"{BASE_URL}/pdf/{encoded_name}"
        try:
            r = requests.get(url, stream=True, timeout=5)
            status = "[PASS]" if r.status_code == 200 else f"[FAIL ({r.status_code})]"
            if r.status_code != 200:
                all_pdfs_ok = False
            print(f"{status} {name}")
            print(f"       URL: {url}")
            print(f"       Content-Type: {r.headers.get('content-type')}, Size: {r.headers.get('content-length')} bytes\n")
        except Exception as e:
            print(f"[ERROR] {name}: {e}\n")
            all_pdfs_ok = False

    print("=" * 75)
    print("2. TESTING LIVE API /ask & CITATION DEEP-LINK ENRICHMENT (#page=X)")
    print("=" * 75)

    for i, t in enumerate(test_queries, 1):
        print(f"\n--- Query Test {i}: {t['query'][:65]}... ---")
        payload = {
            "query": t["query"],
            "jurisdiction": t.get("jurisdiction", "all"),
        }
        try:
            r = requests.post(f"{BASE_URL}/ask", json=payload, timeout=60)
            if r.status_code != 200:
                print(f"[FAIL] Ask API Error {r.status_code}: {r.text[:200]}")
                continue
            
            data = r.json()
            citations = data.get("citations", [])
            print(f"Answer received (Length: {len(data.get('answer', ''))} chars). Citations: {len(citations)}")
            
            found_deep_links = 0
            for cit in citations:
                src = cit.get("source") or cit.get("title", "")
                sec = cit.get("section", "")
                page = cit.get("page_number")
                pdf_url = cit.get("pdf_url")
                pdf_file = cit.get("pdf_filename")
                
                print(f"  * Source: {src}")
                print(f"    Section: {sec}")
                print(f"    Page Number: {page}")
                print(f"    PDF Filename: {pdf_file}")
                print(f"    Deep-Link PDF URL: {pdf_url}")
                
                if pdf_url and "#page=" in pdf_url:
                    found_deep_links += 1
                    base_pdf = pdf_url.split("#")[0]
                    res = requests.get(base_pdf, stream=True, timeout=5)
                    print(f"    -> PDF Access Status: {res.status_code} ({'OK' if res.status_code == 200 else 'FAILED'})")
                print()
                
            if found_deep_links > 0:
                print(f"[PASS] Deep-link verification passed for Query {i} ({found_deep_links}/{len(citations)} citations have #page=X deep links)")
            else:
                print(f"[WARN] No #page= deep links generated for Query {i}")
                
        except Exception as e:
            print(f"[ERROR] Exception running Query {i}: {e}")

if __name__ == "__main__":
    run_tests()
