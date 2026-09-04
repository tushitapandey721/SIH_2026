"""TKDL (Traditional Knowledge Digital Library) Prior-Art Pointer Module.

Under Section 3(p) of the Patents Act, 1970 and CSIR-AYUSH guidelines:
Traditional knowledge and aggregations of known properties of traditional components
are not patentable inventions.

This module provides a structured, non-fabricated prior-art pointer directing
applicants to TKDL and explaining why classical formulations face Section 3(p) objections,
along with plausible formulation kalpana, therapeutic IPC classes, and authoritative
First-Schedule source texts to review.
"""

import re
from typing import Any, Dict, List, Optional


CLASSICAL_KEYWORDS = [
    r"classical\s+(?:medicine|formulation|recipe|oil|remedy|ayurvedic|preparation|drug|herb|text)",
    r"\bclassical\b",
    r"traditional\s+(?:knowledge|formulation|medicine|recipe|remedy|ayurvedic|herbal|oil)",
    r"ayurvedic\s+(?:recipe|text|formulation|oil|preparation|medicine|herb)",
    r"grandmother(?:'s)?(?:\s+\w+){0,4}\s+(?:recipe|oil|remedy|cure|formulation)",
    r"ancestral\s+(?:recipe|remedy|oil|formulation)",
    r"ancient\s+(?:text|recipe|manuscript|formulation|ayurvedic)",
    r"charaka",
    r"sushruta",
    r"vagbhata",
    r"ashtanga\s+hridaya",
    r"sahasrayogam",
    r"bhavaprakasha",
    r"sharangadhara",
    r"first\s+schedule",
    r"classical\s+herb",
    r"ayurvedic\s+herb",
    r"unani",
    r"siddha",
    r"sowa-rigpa",
    r"dravyaguna",
    r"taila\s+kalpana",
    r"churna",
    r"asava",
    r"arishta",
    r"ghrita",
    r"bhasma",
    r"rasayana",
]

PATENT_PRIOR_ART_KEYWORDS = [
    r"patent",
    r"patenting",
    r"patentable",
    r"patentability",
    r"can\s+(?:this|someone|anyone|i)\s+(?:else\s+)?patent",
    r"can\s+be\s+patented",
    r"prior\s*art",
    r"prior-art",
    r"already\s+known",
    r"protect\s+(?:it\s+)?from\s+others\s+patenting",
    r"protect\s+from\s+others\s+patenting",
    r"novelty",
    r"anticipat(?:e|ed|ion)",
    r"public\s+domain",
    r"section\s+3\s*\(\s*p\s*\)",
    r"sec(?:tion)?\s*3\s*p",
    r"3\s*\(\s*p\s*\)",
    r"tkdl",
    r"traditional\s+knowledge\s+digital\s+library",
    r"search\s+tkdl",
    r"examiner\s+objection",
    r"first\s+examination\s+report",
    r"fer\s+objection",
]


def is_classical_formulation_query(query: str) -> bool:
    """Checks if a user query refers to classical/traditional formulations or traditional knowledge."""
    if not query:
        return False
    normalized = query.lower()
    return any(re.search(pat, normalized) for pat in CLASSICAL_KEYWORDS)


def detect_tkdl_trigger(query: str, classification: Optional[str] = None) -> bool:
    """Trigger ONLY when:
    1. The query involves patentability/prior-art language.
    2. AND the formulation classification is 'classical_medicine' or explicitly classical.
    """
    if not query:
        return False

    normalized = query.lower()

    # 1. Must touch on patentability or prior-art language
    has_patent_or_prior_art = any(re.search(pat, normalized) for pat in PATENT_PRIOR_ART_KEYWORDS)
    if not has_patent_or_prior_art:
        return False

    # 2. AND must involve classical/traditional formulation or traditional knowledge
    is_classical = (classification == "classical_medicine") or is_classical_formulation_query(normalized)

    return bool(is_classical and has_patent_or_prior_art)


def extract_tkdl_hints(query: str) -> Dict[str, Any]:
    """Derive plausible TKDL formulation categories, therapeutic areas, and IPC classes.

    NOTE: We NEVER fabricate fictitious TKDL accession numbers. All classifications
    are standard IPC classes, classical Ayurvedic Kalpanas, and First-Schedule texts.
    """
    normalized = query.lower() if query else ""

    # 1. Formulation Kalpana (Ayurvedic Category)
    kalpana_title = "Classical Polyherbal Formulation"
    kalpana_desc = "Formulation based on classical Ayurvedic pharmaceutical processing (Kalpana)."

    if any(w in normalized for w in ["oil", "taila", "thailam", "tailam"]):
        kalpana_title = "Taila Kalpana (Medicated Oils / Lipid Formulations)"
        kalpana_desc = "Vegetable oil (commonly sesame, coconut, or mustard) processed with herbal paste (Kalka) and herbal decoctions (Kwatha)."
    elif any(w in normalized for w in ["ghee", "ghrita", "ghritam"]):
        kalpana_title = "Ghrita Kalpana (Medicated Clarified Butter)"
        kalpana_desc = "Cow's clarified butter processed with decoctions and fine pastes of herbs for enhanced bioavailability across the blood-brain barrier."
    elif any(w in normalized for w in ["powder", "churna", "churnam"]):
        kalpana_title = "Churna Kalpana (Fine Herbal Powders)"
        kalpana_desc = "Dried herbal ingredients pulverized and sieved to fine particle size."
    elif any(w in normalized for w in ["syrup", "asava", "arishta", "fermented"]):
        kalpana_title = "Asava & Arishta (Self-generated Herbal Fermentations)"
        kalpana_desc = "Hydroalcoholic herbal preparations fermented naturally with Woodfordia fruticosa (Dhataki) flowers."
    elif any(w in normalized for w in ["paste", "lepa", "poultice"]):
        kalpana_title = "Lepa Kalpana (Topical Pastes & External Applications)"
        kalpana_desc = "Fine herbal paste applied topically on the skin for localized action."
    elif any(w in normalized for w in ["tablet", "vati", "gutika", "pill"]):
        kalpana_title = "Vati / Gutika (Classical Herbal Tablets / Pills)"
        kalpana_desc = "Compounded herbal mass rolled into pills using binding exudates or honey."
    elif any(w in normalized for w in ["rasayana", "avaleha", "jam", "electuary"]):
        kalpana_title = "Avaleha / Rasayana (Herbal Jams & Electuaries)"
        kalpana_desc = "Semisolid preparation prepared with jaggery/sugar base and herbal decoctions."
    elif any(w in normalized for w in ["decoction", "kwatha", "kashaya", "kashayam"]):
        kalpana_title = "Kwatha / Kashayam Kalpana (Aqueous Decoctions)"
        kalpana_desc = "Concentrated boiling-water extract of coarse herbal parts."

    # 2. Therapeutic Domain & IPC Concordance
    therapeutic_area = "General Therapeutics in Classical AYUSH Formulations"
    ipc_classes: List[Dict[str, str]] = [
        {
            "code": "A61K 36/00",
            "description": "Medicinal preparations of undetermined constitution containing material from plants (herbal medicines).",
        }
    ]

    if any(w in normalized for w in ["joint", "arthritis", "sandhi", "pain", "knee", "inflammation", "rheumat"]):
        therapeutic_area = "Sandhivata & Amavata (Joint Disorders & Musculoskeletal Inflammation)"
        ipc_classes.extend([
            {
                "code": "A61P 19/02",
                "description": "Anti-arthritics / remedies for diseases of the musculoskeletal system.",
            },
            {
                "code": "A61P 29/00",
                "description": "Non-central analgesics, antipyretics or anti-inflammatory agents.",
            },
        ])
    elif any(w in normalized for w in ["skin", "eczema", "psoriasis", "twak", "wound", "burn", "kushta"]):
        therapeutic_area = "Kushta & Twak Vikara (Dermatological Disorders & Wound Healing)"
        ipc_classes.extend([
            {
                "code": "A61P 17/00",
                "description": "Dermatological preparations / remedies for skin diseases.",
            },
            {
                "code": "A61K 8/97",
                "description": "Cosmetics or toilet preparations containing plant extracts.",
            },
        ])
    elif any(w in normalized for w in ["hair", "kesha", "keshya", "dandruff", "scalp", "alopecia"]):
        therapeutic_area = "Keshya (Hair Care, Scalp Disorders & Follicular Health)"
        ipc_classes.extend([
            {
                "code": "A61K 8/97",
                "description": "Cosmetics or toilet preparations containing plant extracts.",
            },
            {
                "code": "A61P 17/14",
                "description": "Drugs for treating baldness or promoting hair growth.",
            },
        ])
    elif any(w in normalized for w in ["digest", "gut", "acidity", "liver", "yakrit", "agni", "constipat", "stomach"]):
        therapeutic_area = "Agnimandya & Yakrit Vikara (Gastrointestinal & Hepatic Disorders)"
        ipc_classes.extend([
            {
                "code": "A61P 1/04",
                "description": "Treatment of peptic ulcers or hyperacidity.",
            },
            {
                "code": "A61P 1/16",
                "description": "Drugs for disorders of the liver or the biliary system.",
            },
        ])
    elif any(w in normalized for w in ["cough", "cold", "asthma", "respiratory", "kasa", "swasa", "bronch"]):
        therapeutic_area = "Kasa & Swasa (Respiratory Disorders & Bronchial Conditions)"
        ipc_classes.extend([
            {
                "code": "A61P 11/00",
                "description": "Drugs for disorders of the respiratory system.",
            },
            {
                "code": "A61P 11/06",
                "description": "Antiasthmatics.",
            },
        ])
    elif any(w in normalized for w in ["diabetes", "sugar", "prameha", "madhumeha", "metabolic"]):
        therapeutic_area = "Prameha & Madhumeha (Metabolic Disorders & Blood Sugar Regulation)"
        ipc_classes.append({
            "code": "A61P 3/10",
            "description": "Drugs for treating diabetes mellitus.",
        })

    # 3. First-Schedule Authoritative Source Texts where Prior Art is Documented
    classical_texts = [
        "Charaka Samhita (Chikitsa Sthana) — foundational textbook of Ayurvedic internal medicine",
        "Sushruta Samhita — classic treatise on therapeutics, surgical lore, and medicinal oils",
        "Ashtanga Hridaya of Vagbhata — comprehensive synthesis of classical formulations",
        "Ayurvedic Formulary of India (AFI), Parts I & II — official statutory standard under Section 3(a) of D&C Act",
    ]
    if "kerala" in normalized or "oil" in normalized or "taila" in normalized:
        classical_texts.insert(2, "Sahasrayogam — authoritative text heavily cited in Kerala traditional practice for oils & kashayams")
    if "unani" in normalized:
        classical_texts = [
            "National Formulary of Unani Medicine (NFUM)",
            "Al-Qanoon fi al-Tibb (The Canon of Medicine) of Ibn Sina (Avicenna)",
            "Kitab al-Hawi fi al-Tibb of Al-Razi (Rhazes)",
            "Bayaz-e-Kabir",
        ]
    elif "siddha" in normalized:
        classical_texts = [
            "Siddha Formulary of India (SFI)",
            "Agathiyar Vaidya Rathina Churukkam",
            "Therayar Maha Karisal",
            "Bogar 7000",
        ]

    # 4. Extract meaningful search keywords (without fabricating record IDs)
    keywords: List[str] = []
    # Check for known botanical or formulation terms
    botanical_candidates = [
        "turmeric", "curcuma", "haridra", "neem", "azadirachta", "ashwagandha",
        "withania", "tulsi", "ocimum", "ginger", "zingiber", "garlic", "sesame",
        "tila", "coconut", "amla", "emblica", "triphala", "brahmi", "bacopa",
        "guggulu", "commiphora", "shallaki", "boswellia", "castor", "eranda",
    ]
    for b in botanical_candidates:
        if b in normalized:
            keywords.append(b.capitalize())

    if not keywords:
        keywords = ["Classical Ayurvedic preparation", kalpana_title.split(" (")[0]]

    return {
        "formulation_category": kalpana_title,
        "formulation_description": kalpana_desc,
        "therapeutic_area": therapeutic_area,
        "ipc_classes": ipc_classes,
        "classical_source_texts": classical_texts,
        "search_keywords": keywords,
        "is_simulated_search": False,
    }


def build_tkdl_pointer_payload(query: str, classification: Optional[str] = None) -> Dict[str, Any]:
    """Build the comprehensive, structured TKDL Prior-Art Pointer payload."""
    if not detect_tkdl_trigger(query, classification):
        return {
            "triggered": False,
            "message": "Query does not involve classical traditional knowledge patentability or prior-art search.",
        }

    hints = extract_tkdl_hints(query)

    return {
        "triggered": True,
        "title": "Check Prior Art in TKDL (Traditional Knowledge Digital Library)",
        "subtitle": "Statutory Prior-Art Guidance under Section 3(p) of the Patents Act, 1970",
        "official_portal_url": "https://www.tkdl.res.in",
        "statutory_provision": "Section 3(p), The Patents Act, 1970",
        "statutory_text": (
            "The following are not inventions within the meaning of this Act: "
            "(p) an invention which in effect, is traditional knowledge or which is "
            "an aggregation or duplication of known properties of traditionally known component or components."
        ),
        "why_relevant": (
            "Classical formulations handed down through generations, family recipes, or derived from ancient "
            "texts belong to the public domain. Under Indian patent law (Section 3(p)) and international patent "
            "regimes, an applicant cannot obtain a patent on classical formulations or mere mixtures of traditionally "
            "known herbs unless significant, non-obvious synergistic biological efficacy is experimentally established."
        ),
        "access_notice": (
            "TKDL is a restricted-access digital repository established jointly by CSIR and the Ministry of AYUSH. "
            "It transcribes and classifies over 2.5 lakh classical formulations into 5 international languages using "
            "the International Patent Classification (IPC). Under bilateral Access Agreements, direct search access is "
            "reserved for Patent Examiners (IPO, USPTO, EPO, JPO, etc.) during examination to prevent wrongful patents. "
            "Individual applicants cannot directly query the full database like a public search engine."
        ),
        "hints": hints,
        "patent_examiner_workflow": [
            {
                "step": "1. Prior-Art Cross Reference",
                "detail": (
                    "When a patent application claiming traditional medicinal herbs is filed, the Patent Examiner searches "
                    "the TKDL database using IPC concordance codes (e.g., A61K 36/00, A61P 19/02) and Sanskrit/botanical keywords."
                ),
            },
            {
                "step": "2. Mandatory Section 3(p) Objection",
                "detail": (
                    "If the composition, processing method, or therapeutic indication is found in classical texts catalogued "
                    "in TKDL (e.g. Charaka Samhita, AFI), the examiner issues a First Examination Report (FER) objection under Section 3(p)."
                ),
            },
            {
                "step": "3. Overcoming the Objection (Legal Standard)",
                "detail": (
                    "To overcome Section 3(p), the applicant cannot rely on traditional use. The applicant must submit rigorous "
                    "comparative experimental data demonstrating a surprising, non-obvious synergistic effect between specific standardized "
                    "extracts or a truly novel, non-obvious delivery system beyond mere classical aggregation."
                ),
            },
        ],
        "recommended_next_steps": [
            "Inspect authoritative First Schedule texts (e.g., Ayurvedic Formulary of India) for identical classical formulations.",
            "Engage a registered Indian Patent Agent to conduct a freedom-to-operate / prior-art clearance search using the TKDL IPC Concordance.",
            "If commercializing without patent monopoly, consider protection via Trade Secret or Proprietary Brand Trademark (Class 5).",
        ],
        "case_study": HISTORICAL_CASE_STUDY,
    }


HISTORICAL_CASE_STUDY: Dict[str, Any] = {
    "triggered": True,
    "title": "Historical Precedents: Turmeric & Neem Biopiracy Revocations",
    "subtitle": "Statutory Context for Section 3(p) & TKDL Defensive Prior-Art Documentation",
    "turmeric_case": {
        "title": "TURMERIC CASE (USPTO — US Patent 5,401,504)",
        "patent_number": "US Patent 5,401,504",
        "jurisdiction": "USPTO (United States)",
        "year_granted": "1995",
        "year_revoked": "1997",
        "facts": (
            "In 1995, the US Patent and Trademark Office granted US Patent 5,401,504 to the University of Mississippi "
            "Medical Center for turmeric powder's wound-healing use. India's CSIR filed a re-examination request in 1996 "
            "with 32 prior-art references from traditional and scientific literature, and the USPTO revoked the patent "
            "in 1997 after finding the use was already known traditional knowledge, not a novel invention."
        ),
    },
    "neem_case": {
        "title": "NEEM CASE (EPO — EP 436257)",
        "patent_number": "EP 436257",
        "jurisdiction": "EPO (European Patent Office)",
        "year_granted": "1994",
        "year_revoked": "2000 (upheld on final appeal 2005)",
        "facts": (
            "In 1994, the European Patent Office granted a patent (EP 436257) to the US Department of Agriculture "
            "and W.R. Grace for a neem-based fungicide. Following opposition on grounds that neem's antifungal use "
            "was centuries-old Indian traditional knowledge, the EPO revoked the patent in 2000, a decision upheld "
            "on final appeal in 2005 — the world's first patent revoked specifically on biopiracy grounds."
        ),
    },
    "closing_line": (
        "These cases are part of why Section 3(p) of the Patents Act, 1970 excludes traditional knowledge from "
        "patentability, and why the Traditional Knowledge Digital Library (TKDL) exists — to document India's "
        "traditional knowledge so it can be used as prior art before a wrongful patent is even granted, rather than fought after the fact."
    ),
    "source_footnote": (
        "Sources: WIPO Traditional Knowledge Case Studies (WIPO/GRTKF); USPTO Reexamination Certificate B1 5,401,504; "
        "EPO Opposition Decision EP 0436257 B1 (Revocation upheld on appeal 2005). Well-documented public historical patent office records."
    ),
}


def get_case_study_payload(query: str, classification: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Returns the historical Turmeric/Neem case-study payload if query touches classical patentability."""
    if not detect_tkdl_trigger(query, classification):
        return None
    return HISTORICAL_CASE_STUDY

