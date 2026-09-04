"""Comprehensive production-readiness legal retrieval evaluation suite (52 queries).

Covers:
- 32 baseline benchmark queries (16 exact section, 16 paraphrased)
- 20 new paraphrased queries (total 52 queries)
- Regression tests for Patents Act Section 2 definitions (2(1)(j), 2(1)(ja), 2(1)(l), 2(1)(ta))
- Regression tests for International Treaties (Nagoya Art 6, TRIPS Art 27, CBD Art 15, PCT Art 8)
"""

import sys
import json
import time
from pathlib import Path
from typing import List, Dict, Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

from app.retrieval.retrieve import retrieve
from app.llm.rag import generate_grounded_answer

BENCHMARK_QUERIES: List[Dict[str, Any]] = [
    # =========================================================================
    # PART 1: 32 BASELINE QUERIES
    # =========================================================================
    # --- Category 1: Patents Act Section 3(p) & Traditional Knowledge ---
    {
        "id": "Q01_BASE",
        "category": "Patents / Traditional Knowledge (3(p))",
        "query_type": "exact_section",
        "query": "Can traditional knowledge be patented under Section 3(p) of the Patents Act?",
        "jurisdiction": "national",
        "gold_doc": "Patents Act",
        "gold_section": "3(p)",
        "gold_keywords": ["Section 3(p)", "traditional knowledge", "known properties", "component"],
    },
    {
        "id": "Q02_BASE",
        "category": "Patents / Traditional Knowledge (3(p))",
        "query_type": "exact_section",
        "query": "What does Section 3(p) of the Patents Act prohibit regarding traditional knowledge?",
        "jurisdiction": "national",
        "gold_doc": "Patents Act",
        "gold_section": "3(p)",
        "gold_keywords": ["Section 3(p)", "traditional knowledge", "aggregation", "duplication"],
    },
    {
        "id": "Q03_BASE",
        "category": "Patents / Traditional Knowledge (3(p))",
        "query_type": "paraphrased",
        "query": "Can an old Ayurvedic remedy receive a patent under Indian law?",
        "jurisdiction": "national",
        "gold_doc": "Patents Act",
        "gold_section": "3(p)",
        "gold_keywords": ["Section 3(p)", "traditional knowledge", "known properties", "not patentable"],
    },
    {
        "id": "Q04_BASE",
        "category": "Patents / Traditional Knowledge (3(p))",
        "query_type": "paraphrased",
        "query": "Is an invention based on known Ayurvedic properties patentable?",
        "jurisdiction": "national",
        "gold_doc": "Patents Act",
        "gold_section": "3(p)",
        "gold_keywords": ["Section 3(p)", "known properties", "traditional knowledge"],
    },
    {
        "id": "Q05_BASE",
        "category": "Patents / Traditional Knowledge (3(p))",
        "query_type": "paraphrased",
        "query": "Why does Indian patent law exclude traditional medicinal knowledge from being patented?",
        "jurisdiction": "national",
        "gold_doc": "Patents Act",
        "gold_section": "3(p)",
        "gold_keywords": ["Section 3(p)", "traditional knowledge", "public domain", "known properties"],
    },
    {
        "id": "Q06_BASE",
        "category": "Patents / Traditional Knowledge (3(p))",
        "query_type": "paraphrased",
        "query": "Is a classical Ayurvedic formulation patentable?",
        "jurisdiction": "national",
        "gold_doc": "Patents Act",
        "gold_section": "3(p)",
        "gold_keywords": ["Section 3(p)", "traditional knowledge", "Rule 158B", "known properties"],
    },

    # --- Category 2: Patents Act Other Statutory Exclusions (3(d), 3(e)) ---
    {
        "id": "Q07_BASE",
        "category": "Patents / Statutory Exclusions (3(d), 3(e))",
        "query_type": "exact_section",
        "query": "What is the requirement for patenting a new form of a known substance under Section 3(d)?",
        "jurisdiction": "national",
        "gold_doc": "Patents Act",
        "gold_section": "3(d)",
        "gold_keywords": ["Section 3(d)", "enhanced efficacy", "known substance", "therapeutic"],
    },
    {
        "id": "Q08_BASE",
        "category": "Patents / Statutory Exclusions (3(d), 3(e))",
        "query_type": "exact_section",
        "query": "Does Section 3(e) prevent patenting a mere admixture of known herbal extracts?",
        "jurisdiction": "national",
        "gold_doc": "Patents Act",
        "gold_section": "3(e)",
        "gold_keywords": ["Section 3(e)", "admixture", "aggregation of properties"],
    },

    # --- Category 3: AYUSH Drug Regulation (D&C Act & Rules) ---
    {
        "id": "Q09_BASE",
        "category": "AYUSH / Drug Regulation",
        "query_type": "exact_section",
        "query": "What proof is required under Rule 158-B to classify an ASU drug as proprietary rather than classical?",
        "jurisdiction": "national",
        "gold_doc": "Drugs and Cosmetics",
        "gold_section": "158",
        "gold_keywords": ["Rule 158B", "patent or proprietary", "First Schedule", "authoritative books"],
    },
    {
        "id": "Q10_BASE",
        "category": "AYUSH / Drug Regulation",
        "query_type": "paraphrased",
        "query": "What evidence must an Ayurvedic company submit to get a license for a proprietary ASU medicine?",
        "jurisdiction": "national",
        "gold_doc": "Drugs and Cosmetics",
        "gold_section": "158",
        "gold_keywords": ["Rule 158B", "licensing", "safety", "pilot study", "First Schedule"],
    },
    {
        "id": "Q11_BASE",
        "category": "AYUSH / Drug Regulation",
        "query_type": "exact_section",
        "query": "What are the penalties for manufacturing adulterated Ayurvedic drugs under Section 33EEC?",
        "jurisdiction": "national",
        "gold_doc": "Drugs and Cosmetics",
        "gold_section": "33EE",
        "gold_keywords": ["33EEC", "adulterated", "imprisonment", "fine"],
    },
    {
        "id": "Q12_BASE",
        "category": "AYUSH / Drug Regulation",
        "query_type": "exact_section",
        "query": "What mandatory information must appear on the container of an Ayurvedic drug under Rule 161?",
        "jurisdiction": "national",
        "gold_doc": "Drugs and Cosmetics",
        "gold_section": "161",
        "gold_keywords": ["Rule 161", "labelling", "ingredients", "batch number"],
    },

    # --- Category 4: Biodiversity & Access Benefit Sharing (BDA 2002 / 2023) ---
    {
        "id": "Q13_BASE",
        "category": "Biodiversity / ABS",
        "query_type": "exact_section",
        "query": "Does an entity need National Biodiversity Authority approval before applying for a patent under Section 6 of the Biological Diversity Act?",
        "jurisdiction": "national",
        "gold_doc": "Biological Diversity",
        "gold_section": "6",
        "gold_keywords": ["Section 6", "National Biodiversity Authority", "prior approval", "patent"],
    },
    {
        "id": "Q14_BASE",
        "category": "Biodiversity / ABS",
        "query_type": "paraphrased",
        "query": "Does an Ayurvedic company need approval before using a biological resource collected in India?",
        "jurisdiction": "national",
        "gold_doc": "Biological Diversity",
        "gold_section": "3",
        "gold_keywords": ["Section 3", "Section 7", "NBA", "State Biodiversity Board", "prior approval"],
    },
    {
        "id": "Q15_BASE",
        "category": "Biodiversity / ABS",
        "query_type": "exact_section",
        "query": "Are local vaids and hakims exempt from giving prior intimation to State Biodiversity Boards under Section 7 of the Biological Diversity Act?",
        "jurisdiction": "national",
        "gold_doc": "Biological Diversity",
        "gold_section": "7",
        "gold_keywords": ["Section 7", "vaids", "hakims", "exempt", "State Biodiversity Board"],
    },

    # --- Category 5: International Treaties ---
    {
        "id": "Q16_BASE",
        "category": "International Treaties",
        "query_type": "exact_section",
        "query": "What are the Prior Informed Consent requirements under Article 6 of the Nagoya Protocol?",
        "jurisdiction": "international",
        "gold_doc": "Nagoya",
        "gold_section": "6",
        "gold_keywords": ["Article 6", "Prior Informed Consent", "Access to Genetic Resources"],
    },
    {
        "id": "Q17_BASE",
        "category": "International Treaties",
        "query_type": "exact_section",
        "query": "How does Article 27 of the TRIPS Agreement define patentable subject matter?",
        "jurisdiction": "international",
        "gold_doc": "trips",
        "gold_section": "27",
        "gold_keywords": ["Article 27", "patentable subject matter", "novelty", "inventive step"],
    },
    {
        "id": "Q18_BASE",
        "category": "International Treaties",
        "query_type": "exact_section",
        "query": "What is the priority claim mechanism under Article 8 of the Patent Cooperation Treaty?",
        "jurisdiction": "international",
        "gold_doc": "PCT",
        "gold_section": "8",
        "gold_keywords": ["Article 8", "Claiming Priority", "Paris Convention"],
    },
    {
        "id": "Q19_BASE",
        "category": "International Treaties",
        "query_type": "exact_section",
        "query": "What mandatory patent disclosure requirement is established under Article 3 of the WIPO GRATK Treaty?",
        "jurisdiction": "international",
        "gold_doc": "WIPO",
        "gold_section": "3",
        "gold_keywords": ["Article 3", "mandatory disclosure", "genetic resources", "traditional knowledge"],
    },
    {
        "id": "Q20_BASE",
        "category": "International Treaties",
        "query_type": "paraphrased",
        "query": "How does the Convention on Biological Diversity regulate sovereign access to genetic resources?",
        "jurisdiction": "international",
        "gold_doc": "Biological Diversity",
        "gold_section": "15",
        "gold_keywords": ["Article 15", "sovereign rights", "Access to Genetic Resources"],
    },

    # --- Category 6: Patents Act Novelty & Inventive Step (Section 2 Definitions) ---
    {
        "id": "Q21_BASE",
        "category": "Patents / General Standards",
        "query_type": "exact_section",
        "query": "How is an inventive step defined under Section 2(1)(ja) of the Patents Act?",
        "jurisdiction": "national",
        "gold_doc": "Patents Act",
        "gold_section": "2(1)(ja)",
        "gold_keywords": ["2(1)(ja)", "inventive step", "technical advance", "economic significance"],
    },
    {
        "id": "Q22_BASE",
        "category": "Patents / General Standards",
        "query_type": "paraphrased",
        "query": "What is the legal standard for proving non-obviousness and technical advancement in Indian patent law?",
        "jurisdiction": "national",
        "gold_doc": "Patents Act",
        "gold_section": "2(1)(ja)",
        "gold_keywords": ["Section 2(1)(ja)", "inventive step", "technical advance", "person skilled in the art"],
    },
    {
        "id": "Q23_BASE",
        "category": "Patents / General Standards",
        "query_type": "paraphrased",
        "query": "What constitutes prior art that destroys the novelty of a patent application in India?",
        "jurisdiction": "national",
        "gold_doc": "Patents Act",
        "gold_section": "2(1)(l)",
        "gold_keywords": ["Section 2(1)(l)", "new invention", "anticipated by publication", "public domain"],
    },
    {
        "id": "Q24_BASE",
        "category": "Patents / General Standards",
        "query_type": "exact_section",
        "query": "What qualifies as an invention under Section 2(1)(j) of the Patents Act?",
        "jurisdiction": "national",
        "gold_doc": "Patents Act",
        "gold_section": "2(1)(j)",
        "gold_keywords": ["2(1)(j)", "invention", "new product or process", "industrial application"],
    },

    # --- Category 7: Phytopharmaceuticals Guidance ---
    {
        "id": "Q25_BASE",
        "category": "AYUSH / Phytopharmaceuticals",
        "query_type": "paraphrased",
        "query": "What safety and clinical data is required to develop a phytopharmaceutical drug in India?",
        "jurisdiction": "national",
        "gold_doc": "Phytopharmaceutical",
        "gold_section": "Phyto",
        "gold_keywords": ["Phytopharmaceutical", "clinical trial", "fraction", "safety"],
    },

    # --- Category 8: Trade Marks, GI, DMR Act ---
    {
        "id": "Q26_BASE",
        "category": "Trade Marks",
        "query_type": "exact_section",
        "query": "What are the absolute grounds for refusal of trademark registration under Section 9 of the Trade Marks Act?",
        "jurisdiction": "national",
        "gold_doc": "Trade Marks",
        "gold_section": "9",
        "gold_keywords": ["Section 9", "absolute grounds", "refusal", "distinctive character"],
    },
    {
        "id": "Q27_BASE",
        "category": "Trade Marks",
        "query_type": "paraphrased",
        "query": "Can an Ayurvedic pharmaceutical company register a descriptive Sanskrit disease name as a trademark?",
        "jurisdiction": "national",
        "gold_doc": "Trade Marks",
        "gold_section": "9",
        "gold_keywords": ["Section 9", "descriptive", "customary in the current language", "distinctiveness"],
    },
    {
        "id": "Q28_BASE",
        "category": "Geographical Indications",
        "query_type": "paraphrased",
        "query": "How can an Ayurvedic producer register as an authorized user of a Geographical Indication for a regional herbal product?",
        "jurisdiction": "national",
        "gold_doc": "Geographical Indications",
        "gold_section": "8",
        "gold_keywords": ["authorized user", "registration", "Geographical Indications"],
    },
    {
        "id": "Q29_BASE",
        "category": "Consumer Protection / DMR Act",
        "query_type": "paraphrased",
        "query": "What legal prohibitions exist against misleading advertisements claiming miraculous cures for Ayurvedic remedies?",
        "jurisdiction": "national",
        "gold_doc": "Magic Remedies",
        "gold_section": "4",
        "gold_keywords": ["misleading advertisements", "magic remedies", "prohibition"],
    },
    {
        "id": "Q30_BASE",
        "category": "Biodiversity / ABS",
        "query_type": "paraphrased",
        "query": "What are the benefit-sharing obligations for Indian companies commercially utilizing wild bio-resources under BDA 2024 Rules?",
        "jurisdiction": "national",
        "gold_doc": "Biological Diversity",
        "gold_section": "Rules",
        "gold_keywords": ["benefit sharing", "commercial utilization", "Rules 2024"],
    },

    # --- Category 9: Negative & Regulatory Disambiguation ---
    {
        "id": "Q31_BASE",
        "category": "Negative / Patentable Novel Molecules",
        "query_type": "paraphrased",
        "query": "Can a novel, structurally modified synthetic derivative of a chemical compound found in an Ayurvedic plant be patented in India?",
        "jurisdiction": "national",
        "gold_doc": "Patents Act",
        "gold_section": "2(1)(j)",
        "gold_keywords": ["patentable", "synthetic derivative", "Section 2(1)(j)", "Section 3(d)"],
    },
    {
        "id": "Q32_BASE",
        "category": "Negative / Regulatory vs IP",
        "query_type": "paraphrased",
        "query": "Does obtaining an ASU drug manufacturing licence from AYUSH State Licensing Authority confer any patent rights on the formulation?",
        "jurisdiction": "national",
        "gold_doc": "Drugs and Cosmetics",
        "gold_section": "158",
        "gold_keywords": ["licence", "regulatory permission", "does not confer patent", "Rule 158B"],
    },

    # =========================================================================
    # PART 2: 20 NEW PARAPHRASED QUERIES
    # =========================================================================
    {
        "id": "Q33_NEW",
        "category": "Patents / Traditional Knowledge (3(p))",
        "query_type": "paraphrased",
        "query": "Can a traditional herbal remedy handed down through generations be granted a patent in India?",
        "jurisdiction": "national",
        "gold_doc": "Patents Act",
        "gold_section": "3(p)",
        "gold_keywords": ["Section 3(p)", "traditional knowledge", "not patentable", "known properties"],
    },
    {
        "id": "Q34_NEW",
        "category": "Patents / Statutory Exclusions (3(d), 3(e))",
        "query_type": "paraphrased",
        "query": "What standard does the Patent Office apply when evaluating whether an Ayurvedic herb combination is merely an admixture?",
        "jurisdiction": "national",
        "gold_doc": "Patents Act",
        "gold_section": "3(e)",
        "gold_keywords": ["Section 3(e)", "admixture", "aggregation of properties"],
    },
    {
        "id": "Q35_NEW",
        "category": "Patents / Statutory Exclusions (3(d), 3(e))",
        "query_type": "paraphrased",
        "query": "Is a modified plant extract with significantly enhanced therapeutic efficacy excluded under patent law?",
        "jurisdiction": "national",
        "gold_doc": "Patents Act",
        "gold_section": "3(d)",
        "gold_keywords": ["Section 3(d)", "enhanced efficacy", "known substance"],
    },
    {
        "id": "Q36_NEW",
        "category": "Patents / General Standards",
        "query_type": "paraphrased",
        "query": "Does prior knowledge documented in ancient Sanskrit Ayurvedic texts destroy novelty for an Indian patent?",
        "jurisdiction": "national",
        "gold_doc": "Patents Act",
        "gold_section": "2(1)(l)",
        "gold_keywords": ["Section 2(1)(l)", "Section 3(p)", "prior art", "public domain"],
    },
    {
        "id": "Q37_NEW",
        "category": "Patents / General Standards",
        "query_type": "paraphrased",
        "query": "How can an inventor establish that an Ayurvedic drug modification involves an inventive step?",
        "jurisdiction": "national",
        "gold_doc": "Patents Act",
        "gold_section": "2(1)(ja)",
        "gold_keywords": ["Section 2(1)(ja)", "inventive step", "technical advance", "economic significance"],
    },
    {
        "id": "Q38_NEW",
        "category": "Patents / General Standards",
        "query_type": "paraphrased",
        "query": "Can a company patent a pure isolated active chemical molecule extracted from a traditional plant if it is a new entity?",
        "jurisdiction": "national",
        "gold_doc": "Patents Act",
        "gold_section": "2(1)(ta)",
        "gold_keywords": ["Section 2(1)(ta)", "Section 2(1)(j)", "pharmaceutical substance", "new entity"],
    },
    {
        "id": "Q39_NEW",
        "category": "AYUSH / Drug Regulation",
        "query_type": "paraphrased",
        "query": "What documentation is necessary to prove an ASU formulation is mentioned in the First Schedule classical treatises?",
        "jurisdiction": "national",
        "gold_doc": "Drugs and Cosmetics",
        "gold_section": "158",
        "gold_keywords": ["Rule 158B", "First Schedule", "authoritative books"],
    },
    {
        "id": "Q40_NEW",
        "category": "Biodiversity / ABS",
        "query_type": "paraphrased",
        "query": "Are commercial manufacturers of herbal medicines required to obtain prior clearance from State Biodiversity Boards?",
        "jurisdiction": "national",
        "gold_doc": "Biological Diversity",
        "gold_section": "7",
        "gold_keywords": ["Section 7", "State Biodiversity Board", "commercial utilization"],
    },
    {
        "id": "Q41_NEW",
        "category": "Biodiversity / ABS",
        "query_type": "paraphrased",
        "query": "Under what circumstances are local folk healers and vaids exempt from notifying biodiversity authorities?",
        "jurisdiction": "national",
        "gold_doc": "Biological Diversity",
        "gold_section": "7",
        "gold_keywords": ["Section 7", "vaids", "hakims", "exempt"],
    },
    {
        "id": "Q42_NEW",
        "category": "Biodiversity / ABS",
        "query_type": "paraphrased",
        "query": "What are the mandatory conditions for obtaining NBA permission before filing a patent based on Indian biological resources?",
        "jurisdiction": "national",
        "gold_doc": "Biological Diversity",
        "gold_section": "6",
        "gold_keywords": ["Section 6", "National Biodiversity Authority", "prior approval"],
    },
    {
        "id": "Q43_NEW",
        "category": "International Treaties",
        "query_type": "paraphrased",
        "query": "What obligations exist under the Nagoya Protocol regarding fair and equitable sharing of monetary benefits?",
        "jurisdiction": "international",
        "gold_doc": "Nagoya",
        "gold_section": "5",
        "gold_keywords": ["Article 5", "fair and equitable", "benefit-sharing"],
    },
    {
        "id": "Q44_NEW",
        "category": "International Treaties",
        "query_type": "paraphrased",
        "query": "How does TRIPS require member nations to protect patentable inventions and microbiological processes?",
        "jurisdiction": "international",
        "gold_doc": "trips",
        "gold_section": "27",
        "gold_keywords": ["Article 27", "microbiological", "patentable subject matter"],
    },
    {
        "id": "Q45_NEW",
        "category": "International Treaties",
        "query_type": "paraphrased",
        "query": "What time limits apply when claiming priority for an international patent application under PCT?",
        "jurisdiction": "international",
        "gold_doc": "PCT",
        "gold_section": "8",
        "gold_keywords": ["Article 8", "Claiming Priority", "time limit"],
    },
    {
        "id": "Q46_NEW",
        "category": "International Treaties",
        "query_type": "paraphrased",
        "query": "What disclosure rules apply to patent applicants utilizing genetic resources under the new WIPO treaty?",
        "jurisdiction": "international",
        "gold_doc": "WIPO",
        "gold_section": "3",
        "gold_keywords": ["Article 3", "mandatory disclosure", "genetic resources"],
    },
    {
        "id": "Q47_NEW",
        "category": "Trade Marks",
        "query_type": "paraphrased",
        "query": "Can a registered trademark for an Ayurvedic medicine be cancelled if it is purely descriptive of the disease?",
        "jurisdiction": "national",
        "gold_doc": "Trade Marks",
        "gold_section": "9",
        "gold_keywords": ["Section 9", "absolute grounds", "descriptive"],
    },
    {
        "id": "Q48_NEW",
        "category": "Geographical Indications",
        "query_type": "paraphrased",
        "query": "What rights does a producer obtain by registering as an authorized user of a Geographical Indication for herbal tea?",
        "jurisdiction": "national",
        "gold_doc": "Geographical Indications",
        "gold_section": "8",
        "gold_keywords": ["authorized user", "exclusive right", "Geographical Indications"],
    },
    {
        "id": "Q49_NEW",
        "category": "Consumer Protection / DMR Act",
        "query_type": "paraphrased",
        "query": "What statutory penalties apply for publishing advertisements that falsely promise miraculous cures for chronic ailments?",
        "jurisdiction": "national",
        "gold_doc": "Magic Remedies",
        "gold_section": "4",
        "gold_keywords": ["magic remedies", "misleading advertisement", "penalties"],
    },
    {
        "id": "Q50_NEW",
        "category": "AYUSH / Drug Regulation",
        "query_type": "paraphrased",
        "query": "What labelling details must appear on a commercial package of Ayurvedic proprietary medicine in India?",
        "jurisdiction": "national",
        "gold_doc": "Drugs and Cosmetics",
        "gold_section": "161",
        "gold_keywords": ["Rule 161", "labelling", "ingredients"],
    },
    {
        "id": "Q51_NEW",
        "category": "Negative / Regulatory vs IP",
        "query_type": "paraphrased",
        "query": "Does a state manufacturing license for an Ayurvedic tablet prevent competing companies from manufacturing the same classical recipe?",
        "jurisdiction": "national",
        "gold_doc": "Drugs and Cosmetics",
        "gold_section": "158",
        "gold_keywords": ["licence", "classical recipe", "does not prevent", "no patent exclusivity"],
    },
    {
        "id": "Q52_NEW",
        "category": "AYUSH / Phytopharmaceuticals",
        "query_type": "paraphrased",
        "query": "What clinical trial and safety data is mandated for developing a purified fraction phytopharmaceutical drug?",
        "jurisdiction": "national",
        "gold_doc": "Phytopharmaceutical",
        "gold_section": "Phyto",
        "gold_keywords": ["Phytopharmaceutical", "clinical trial", "purified fraction"],
    },
]


def run_evaluation() -> Dict[str, Any]:
    print("=" * 100)
    print("RUNNING COMPREHENSIVE PRODUCTION EVALUATION (52 QUERIES)")
    print("=" * 100)

    total_queries = len(BENCHMARK_QUERIES)
    gold_in_pool_count = 0
    top5_hits = 0
    top10_hits = 0
    top20_hits = 0
    reciprocal_ranks = []
    citation_accurate_count = 0

    exact_total = 0
    exact_hits = 0
    exact_mrr_list = []

    paraphrased_total = 0
    paraphrased_hits = 0
    paraphrased_mrr_list = []

    results_log = []

    for idx, item in enumerate(BENCHMARK_QUERIES, start=1):
        q_id = item["id"]
        q_text = item["query"]
        q_type = item["query_type"]
        jurisdiction = item["jurisdiction"]
        gold_doc = item["gold_doc"].lower()
        gold_sec = item["gold_section"].lower()

        t0 = time.time()
        retrieval_res = retrieve(
            query=q_text,
            jurisdiction=jurisdiction,
            dense_top_k=60,
            bm25_top_k=30,
            fused_top_k=60,
            rerank_top_k=5,
            rrf_k=60,
            max_per_doc=3,
        )
        elapsed_retrieval = time.time() - t0

        final_chunks = retrieval_res.get("results", [])
        raw_candidates = retrieval_res.get("raw_candidates", [])

        # Check candidate pool
        pool_rank = None
        for r_idx, c in enumerate(raw_candidates, start=1):
            c_doc = str(c.get("title", "")).lower()
            c_sec = str(c.get("section", "")).lower()
            if gold_doc in c_doc and gold_sec in c_sec:
                pool_rank = r_idx
                break

        in_pool = pool_rank is not None
        if in_pool:
            gold_in_pool_count += 1

        # Check Top 5 rank
        final_rank = None
        for f_idx, c in enumerate(final_chunks, start=1):
            c_doc = str(c.get("title", "")).lower()
            c_sec = str(c.get("section", "")).lower()
            if gold_doc in c_doc and gold_sec in c_sec:
                final_rank = f_idx
                break

        is_hit = final_rank is not None
        if is_hit:
            top5_hits += 1
            top10_hits += 1
            top20_hits += 1
            rr = 1.0 / final_rank
        else:
            rr = 0.0
            if pool_rank and pool_rank <= 10:
                top10_hits += 1
            if pool_rank and pool_rank <= 20:
                top20_hits += 1

        reciprocal_ranks.append(rr)

        # Track exact vs paraphrased
        if q_type == "exact_section":
            exact_total += 1
            if is_hit:
                exact_hits += 1
            exact_mrr_list.append(rr)
        else:
            paraphrased_total += 1
            if is_hit:
                paraphrased_hits += 1
            paraphrased_mrr_list.append(rr)

        # Generate answer and evaluate citation
        rag_output = generate_grounded_answer(q_text, final_chunks)
        answer_text = rag_output.get("answer", "")
        citations = rag_output.get("citations", [])

        # Citation accuracy check
        citation_matches_gold = any(gold_sec in cit.lower() for cit in citations) or (gold_sec in answer_text.lower())
        if citation_matches_gold:
            citation_accurate_count += 1

        print(
            f"[{idx:02d}/{total_queries:02d}] {q_id} ({q_type}) | Pool: {pool_rank or 'MISS':4} | "
            f"Final: {final_rank or 'MISS':4} | Citations: {len(citations)} | Time: {elapsed_retrieval*1000:.1f}ms"
        )
        if not is_hit:
            top_sources = [f"[{c.get('title', '')[:18]} S.{c.get('section', '')[:12]}]" for c in final_chunks[:3]]
            print(f"       -> Query: '{q_text[:70]}...'")
            print(f"       -> Gold Expected: [{gold_doc} / {gold_sec}] | Got Top 3: {top_sources}")

        results_log.append({
            "id": q_id,
            "query": q_text,
            "type": q_type,
            "category": item["category"],
            "pool_rank": pool_rank,
            "final_rank": final_rank,
            "hit_top5": is_hit,
            "reciprocal_rank": rr,
            "citations": citations,
            "answer_preview": answer_text[:200],
        })

    mrr = sum(reciprocal_ranks) / total_queries if total_queries else 0.0
    exact_mrr = sum(exact_mrr_list) / exact_total if exact_total else 0.0
    para_mrr = sum(paraphrased_mrr_list) / paraphrased_total if paraphrased_total else 0.0

    metrics = {
        "total_queries": total_queries,
        "exact_queries_total": exact_total,
        "exact_queries_recall5": exact_hits / exact_total if exact_total else 0.0,
        "exact_queries_mrr": exact_mrr,
        "paraphrased_queries_total": paraphrased_total,
        "paraphrased_queries_recall5": paraphrased_hits / paraphrased_total if paraphrased_total else 0.0,
        "paraphrased_queries_mrr": para_mrr,
        "candidate_pool_recall": gold_in_pool_count / total_queries if total_queries else 0.0,
        "recall_at_5": top5_hits / total_queries if total_queries else 0.0,
        "recall_at_10": top10_hits / total_queries if total_queries else 0.0,
        "recall_at_20": top20_hits / total_queries if total_queries else 0.0,
        "mrr": mrr,
        "citation_accuracy": citation_accurate_count / total_queries if total_queries else 0.0,
    }

    print("\n" + "=" * 100)
    print("FINAL EVALUATION METRICS REPORT")
    print("=" * 100)
    print(f"• Total Queries:                   {total_queries}")
    print(f"• Candidate Pool Recall:           {gold_in_pool_count}/{total_queries} ({metrics['candidate_pool_recall']*100:.1f}%)")
    print(f"• Recall@5 (Top-5 Hit Rate):       {top5_hits}/{total_queries} ({metrics['recall_at_5']*100:.1f}%)")
    print(f"• Recall@10:                       {top10_hits}/{total_queries} ({metrics['recall_at_10']*100:.1f}%)")
    print(f"• Recall@20:                       {top20_hits}/{total_queries} ({metrics['recall_at_20']*100:.1f}%)")
    print(f"• Mean Reciprocal Rank (MRR):      {metrics['mrr']:.4f}")
    print(f"• Exact-Section Recall@5:          {exact_hits}/{exact_total} ({metrics['exact_queries_recall5']*100:.1f}%) [MRR: {exact_mrr:.4f}]")
    print(f"• Paraphrased Recall@5:            {paraphrased_hits}/{paraphrased_total} ({metrics['paraphrased_queries_recall5']*100:.1f}%) [MRR: {para_mrr:.4f}]")
    print(f"• Citation Accuracy:               {citation_accurate_count}/{total_queries} ({metrics['citation_accuracy']*100:.1f}%)")
    print("=" * 100)

    # Save to json
    output_path = PROJECT_ROOT / "eval" / "comprehensive_benchmark_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"metrics": metrics, "queries": results_log}, f, indent=2)
    print(f"Saved complete benchmark results to: {output_path}")

    return metrics


if __name__ == "__main__":
    run_evaluation()
