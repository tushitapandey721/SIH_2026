"""Comprehensive evaluation of the targeted fixes for the 4 failure modes and new regression queries."""

import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

from app.retrieval.retrieve import LegalRetriever
from app.retrieval.query_expansion import expand_legal_query

def run_tests():
    print("=" * 100)
    print("TESTING RETRIEVAL FIXES FOR ALL 4 TARGETED FAILURE MODES & NEW REGRESSION QUERIES")
    print("=" * 100)

    retriever = LegalRetriever()

    TEST_CASES = [
        # --- Failure 1: Rule 161 ---
        {
            "category": "Failure 1: D&C Rule 161",
            "query": "What are the labelling requirements for Ayurvedic drugs under Rule 161?",
            "gold_doc": "Drugs and Cosmetics",
            "gold_sec": "161",
            "jurisdiction": "national",
        },
        {
            "category": "Failure 1: D&C Rule 161 (Regression)",
            "query": "What does Rule 161 of the Drugs and Cosmetics Rules cover?",
            "gold_doc": "Drugs and Cosmetics",
            "gold_sec": "161",
            "jurisdiction": "national",
        },

        # --- Failure 2: GI Section 8 ---
        {
            "category": "Failure 2: GI Act Section 8 (Q27)",
            "query": "What constitutes an authorized user of a registered Geographical Indication under Section 8 of the GI Act?",
            "gold_doc": "Geographical Indications",
            "gold_sec": "8",
            "jurisdiction": "national",
        },
        {
            "category": "Failure 2: GI Act Section 8 (Regression 1)",
            "query": "Section 8 of the Geographical Indications Act",
            "gold_doc": "Geographical Indications",
            "gold_sec": "8",
            "jurisdiction": "national",
        },
        {
            "category": "Failure 2: GI Act Section 8 (Regression 2)",
            "query": "Who can apply for registration of a geographical indication?",
            "gold_doc": "Geographical Indications",
            "gold_sec": "8",
            "jurisdiction": "national",
        },

        # --- Failure 3: GI Agricultural Origin Paraphrases ---
        {
            "category": "Failure 3: GI Agricultural Origin (Q30)",
            "query": "Can authentic regional origin for herbal and agricultural crops be protected as a Geographical Indication?",
            "gold_doc": "Geographical Indications",
            "gold_sec": "8",
            "jurisdiction": "national",
        },
        {
            "category": "Failure 3: GI Agricultural Origin (Paraphrase 1)",
            "query": "How is the geographical origin of agricultural goods protected?",
            "gold_doc": "Geographical Indications",
            "gold_sec": "8",
            "jurisdiction": "national",
        },
        {
            "category": "Failure 3: GI Agricultural Origin (Paraphrase 2)",
            "query": "How are agricultural products linked to a geographical indication?",
            "gold_doc": "Geographical Indications",
            "gold_sec": "8",
            "jurisdiction": "national",
        },
        {
            "category": "Failure 3: GI Agricultural Origin (Paraphrase 3)",
            "query": "What protects products whose reputation comes from their place of origin?",
            "gold_doc": "Geographical Indications",
            "gold_sec": "8",
            "jurisdiction": "national",
        },

        # --- Failure 4: Synthetic Derivatives vs Traditional Knowledge Distinction ---
        {
            "category": "Failure 4: Synthetic Derivative (Q31)",
            "query": "Can a novel, structurally modified synthetic derivative of a chemical compound found in an Ayurvedic plant be patented in India?",
            "gold_doc": "Patents Act",
            "gold_sec": "2(1)(j)",
            "jurisdiction": "national",
        },
        {
            "category": "Failure 4: Synthetic Derivative (Paraphrase 1)",
            "query": "Is a chemically modified derivative of a plant compound patentable if it demonstrates enhanced therapeutic efficacy?",
            "gold_doc": "Patents Act",
            "gold_sec": "3(d)",
            "jurisdiction": "national",
        },
        {
            "category": "Failure 4: Synthetic Derivative (Paraphrase 2)",
            "query": "Can an isolated active alkaloid from an Ayurvedic herb with a novel synthetic modification receive a patent?",
            "gold_doc": "Patents Act",
            "gold_sec": "2(1)(j)",
            "jurisdiction": "national",
        },
        {
            "category": "Failure 4: Synthetic Derivative (Paraphrase 3)",
            "query": "Does a structurally modified molecule derived from a traditional botanical source qualify as an invention with inventive step?",
            "gold_doc": "Patents Act",
            "gold_sec": "2(1)(ja)",
            "jurisdiction": "national",
        },
        {
            "category": "Failure 4: Synthetic Derivative (Paraphrase 4)",
            "query": "What patentability criteria apply to a new synthetic substance synthesized using an Ayurvedic plant extract as precursor?",
            "gold_doc": "Patents Act",
            "gold_sec": "2(1)(j)",
            "jurisdiction": "national",
        },
        {
            "category": "Failure 4: Synthetic Derivative (Paraphrase 5)",
            "query": "Is a novel derivative of a natural phytochemical patentable under Section 2(1)(j) and Section 3(d)?",
            "gold_doc": "Patents Act",
            "gold_sec": "2(1)(j)",
            "jurisdiction": "national",
        },

        # --- Critical Control: Section 3(p) Traditional Knowledge Contrast ---
        {
            "category": "Control: Traditional Knowledge Section 3(p)",
            "query": "What does Section 3(p) of the Patents Act prohibit?",
            "gold_doc": "Patents Act",
            "gold_sec": "3(p)",
            "jurisdiction": "national",
        },
        {
            "category": "Control: Traditional Knowledge Section 3(p) Paraphrase",
            "query": "Is an unmodified classical Ayurvedic herbal formulation patentable under Indian patent law?",
            "gold_doc": "Patents Act",
            "gold_sec": "3(p)",
            "jurisdiction": "national",
        },
    ]

    passed_count = 0
    total_count = len(TEST_CASES)

    for idx, tc in enumerate(TEST_CASES, start=1):
        cat = tc["category"]
        q = tc["query"]
        g_doc = tc["gold_doc"]
        g_sec = tc["gold_sec"]
        j = tc["jurisdiction"]

        print("-" * 100)
        print(f"[{idx:02d}/{total_count:02d}] {cat}")
        print(f"Query: \"{q}\"")
        print(f"Target Gold: [{g_doc}] Section/Rule matching '{g_sec}'")

        t0 = time.perf_counter()
        top_results, diag = retriever.retrieve(q, jurisdiction=j)
        latency_ms = (time.perf_counter() - t0) * 1000

        found_rank = None
        for r_idx, r in enumerate(top_results, start=1):
            is_match = (g_doc.lower() in r.get("title", "").lower() and g_sec.lower() in r.get("section", "").lower())
            if is_match:
                found_rank = r_idx
                break

        if found_rank is not None:
            passed_count += 1
            status_str = f"PASS (Rank {found_rank})"
        else:
            status_str = "FAIL"

        print(f"Status: {status_str} | Latency: {latency_ms:.1f}ms")
        print("Top 3 retrieved passages:")
        for r_idx, r in enumerate(top_results[:3], start=1):
            print(f"   #{r_idx}: [{r.get('title')}] {r.get('section')} (CE Score: {r.get('cross_encoder_raw_score', 0):+.3f})")

    print("\n" + "=" * 100)
    print(f"TEST RESULTS: {passed_count}/{total_count} PASSED ({passed_count/total_count*100:.1f}%)")
    print("=" * 100)

if __name__ == "__main__":
    run_tests()
