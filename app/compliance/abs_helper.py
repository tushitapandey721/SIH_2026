"""Access & Benefit-Sharing (ABS) Compliance Helper for Indian Biological Diversity Law.

Governed by:
- Biological Diversity Act, 2002 (Act No. 18 of 2003) as amended by Biological Diversity (Amendment) Act, 2023 (Act No. 10 of 2023)
- Biological Diversity Rules, 2024 (G.S.R. 306(E), 15 May 2024)
- Biological Diversity (Amendment) Rules, 2025 (G.S.R. 138(E), 24 Feb 2025)
"""

import re
from typing import Dict, Any, Optional, List

# Indian States and Union Territories for state board localization
INDIAN_STATES_BOARDS = {
    "kerala": "Kerala State Biodiversity Board (KSBB)",
    "tamil nadu": "Tamil Nadu State Biodiversity Board (TNSBB)",
    "karnataka": "Karnataka Biodiversity Board (KBB)",
    "maharashtra": "Maharashtra State Biodiversity Board (MSBB)",
    "uttarakhand": "Uttarakhand Biodiversity Board (UBB)",
    "himachal pradesh": "Himachal Pradesh State Biodiversity Board (HPSBB)",
    "madhya pradesh": "Madhya Pradesh State Biodiversity Board (MPSBB)",
    "gujarat": "Gujarat Biodiversity Board (GBB)",
    "rajasthan": "Rajasthan State Biodiversity Board (RSBB)",
    "andhra pradesh": "Andhra Pradesh State Biodiversity Board (APSBB)",
    "telangana": "Telangana State Biodiversity Board (TSBB)",
    "odisha": "Odisha Biodiversity Board (OBB)",
    "west bengal": "West Bengal Biodiversity Board (WBBB)",
    "assam": "Assam State Biodiversity Board (ASBB)",
    "bihar": "Bihar State Biodiversity Board (BSBB)",
    "punjab": "Punjab Biodiversity Board (PBB)",
    "haryana": "Haryana State Biodiversity Board (HSBB)",
    "uttar pradesh": "Uttar Pradesh State Biodiversity Board (UPSBB)",
    "chhattisgarh": "Chhattisgarh State Biodiversity Board (CSBB)",
    "jharkhand": "Jharkhand State Biodiversity Board (JSBB)",
    "goa": "Goa State Biodiversity Board (GSBB)",
    "jammu and kashmir": "Jammu & Kashmir Biodiversity Council (JKBC)",
    "ladakh": "Ladakh Biodiversity Council (LBC)",
    "sikkim": "Sikkim State Biodiversity Board (SSBB)",
    "arunachal pradesh": "Arunachal Pradesh State Biodiversity Board (APSBB)",
    "meghalaya": "Meghalaya State Biodiversity Board (MSBB)",
    "manipur": "Manipur State Biodiversity Board (MSBB)",
    "mizoram": "Mizoram State Biodiversity Board (MSBB)",
    "nagaland": "Nagaland State Biodiversity Board (NSBB)",
    "tripura": "Tripura Biodiversity Board (TBB)",
}

# The 3 structured decision flow questions
ABS_QUESTIONS: List[Dict[str, Any]] = [
    {
        "id": "is_sourced_from_india",
        "question": "Is the biological resource sourced or obtained from within India?",
        "options": [
            {"label": "Yes, sourced in India", "value": True},
            {"label": "No, sourced outside India", "value": False},
        ],
        "help_text": "Sections 2(c), 3(1), and 7(1) of the Biological Diversity Act apply strictly to biological resources occurring in or accessed from India. If sourced abroad, Indian BD Act ABS does not apply.",
    },
    {
        "id": "is_commercial_use",
        "question": "Is the biological resource intended for commercial utilization / export / transfer, or for non-commercial scientific research only?",
        "options": [
            {"label": "Commercial Utilization / Formulation / Export", "value": True},
            {"label": "Research / Bio-survey Only", "value": False},
        ],
        "help_text": "Commercial utilization includes manufacturing, marketing, or exporting products. Pure academic/scientific research carries lighter statutory obligations under the BD Rules.",
    },
    {
        "id": "is_foreign_entity",
        "question": "Is the applicant an Indian citizen / domestic entity, or a foreign entity / NRI / foreign-controlled company?",
        "options": [
            {"label": "Indian Citizen / Domestic Entity", "value": False},
            {"label": "Foreign Entity / NRI / Foreign-Controlled Firm", "value": True},
        ],
        "help_text": "Under Section 3(2) of the BD Act (as amended in 2023), non-citizens, NRIs (Income-tax Act S. 2(30)), and Indian entities controlled by foreigners (Companies Act S. 2(27)) require National Biodiversity Authority (NBA) approval. Domestic entities fall under Section 7 (State Biodiversity Board).",
    },
]


def detect_abs_trigger(query: str) -> bool:
    """Determines whether a user query involves accessing, sourcing, or commercializing biological resources.

    Triggers into the ABS helper in addition to the normal RAG pipeline.
    """
    q = query.lower()

    # 1. Direct ABS statutory / institutional keywords
    abs_keywords = [
        "abs",
        "access and benefit sharing",
        "access & benefit sharing",
        "access and benefit-sharing",
        "access & benefit-sharing",
        "national biodiversity authority",
        "nba approval",
        "nba approval",
        "state biodiversity board",
        "biodiversity board",
        "sbb intimation",
        "biological diversity act",
        "biological diversity amendment",
        "bd act",
        "bda 2002",
        "bda 2023",
        "nagoya protocol",
        "biodiversity management committee",
        "bmc certificate",
        "certificate of origin",
        "form 1",
        "form 2",
        "form 11",
        "form 12",
    ]
    for kw in abs_keywords:
        # Match whole word / phrase
        if re.search(r"\b" + re.escape(kw) + r"\b", q):
            return True

    # 2. Biological resource indicators
    bio_terms = [
        r"\bplant\b",
        r"\bplants\b",
        r"\bherb\b",
        r"\bherbs\b",
        r"\bherbal\b",
        r"\bextract\b",
        r"\bextracts\b",
        r"\bleaf\b",
        r"\bleaves\b",
        r"\broot\b",
        r"\broots\b",
        r"\bbark\b",
        r"\bseed\b",
        r"\bseeds\b",
        r"\bflora\b",
        r"\bfauna\b",
        r"\bmarine organism\b",
        r"\bmedicinal plant\b",
        r"\bbiological resource\b",
        r"\bbio-resource\b",
        r"\bbioresourc\w*",
        r"\bneem\b",
        r"\bashwagandha\b",
        r"\bturmeric\b",
        r"\bbrahmi\b",
        r"\btulsi\b",
        r"\bayurvedic ingredient\b",
        r"\bnatural formulation\b",
    ]

    has_bio_resource = any(re.search(pat, q) for pat in bio_terms)

    # Sourcing indicators
    source_terms = [
        r"\bsourced\b",
        r"\bsourcing\b",
        r"\bcollected\b",
        r"\bcollecting\b",
        r"\bharvested\b",
        r"\bharvesting\b",
        r"\bobtained from\b",
        r"\bprocured from\b",
        r"\bgrown in\b",
        r"\bnative to\b",
        r"\bfrom kerala\b",
        r"\bfrom india\b",
        r"\bfrom western ghats\b",
        r"\bfrom himalayas\b",
        r"\bwild-harvested\b",
        r"\bcultivated\b",
    ]
    has_sourcing = any(re.search(pat, q) for pat in source_terms)

    # Commercialization / export indicators
    commercial_terms = [
        r"\bexport\b",
        r"\bexporting\b",
        r"\bexported\b",
        r"\bcommercial\b",
        r"\bcommercialize\b",
        r"\bcommercializing\b",
        r"\bcommercialisation\b",
        r"\bcommercial utilization\b",
        r"\bsell\b",
        r"\bselling\b",
        r"\bmanufacture\b",
        r"\bmanufacturing\b",
        r"\bsupplement\b",
        r"\bformulation\b",
        r"\bapproval\b",
        r"\bpermission\b",
        r"\blicense\b",
        r"\blicensing\b",
    ]
    has_commercial = any(re.search(pat, q) for pat in commercial_terms)

    # Any Indian state mentioned along with a biological resource
    has_state_sourcing = any(state in q for state in INDIAN_STATES_BOARDS.keys()) and has_bio_resource

    if has_bio_resource and (has_sourcing or has_commercial or has_state_sourcing):
        return True

    return False


def _is_yes(val: Any) -> Optional[bool]:
    """Evaluates boolean or string answers to True/False/None."""
    if val is None:
        return None
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return val == 1
    if isinstance(val, str):
        v = val.strip().lower()
        if v in ("yes", "y", "true", "1", "commercial", "foreign"):
            return True
        if v in ("no", "n", "false", "0", "research", "domestic", "indian"):
            return False
    return None


def detect_state_in_query(text: str) -> Optional[str]:
    """Extracts mentioned Indian State/UT name from text for localized SBB identification."""
    t = text.lower()
    for state in INDIAN_STATES_BOARDS.keys():
        if re.search(r"\b" + re.escape(state) + r"\b", t):
            return state.title()
    return None


def extract_abs_initial_answers(query: str) -> Dict[str, Any]:
    """Infers initial answers and location from query context where unambiguous."""
    q = query.lower()
    answers: Dict[str, Any] = {}

    # Check sourcing location
    detected_state = detect_state_in_query(q)
    if detected_state or "india" in q or "kerala" in q or "western ghats" in q or "himalayas" in q or "domestic" in q:
        answers["is_sourced_from_india"] = True
    elif "outside india" in q or "foreign country" in q or "imported from" in q or "sourced abroad" in q:
        answers["is_sourced_from_india"] = False

    # Check commercial purpose vs research
    if any(k in q for k in ["export", "commercial", "sell", "manufacture", "supplement", "market", "product"]):
        answers["is_commercial_use"] = True
    elif any(k in q for k in ["research only", "pure research", "scientific study", "academic study", "lab trial"]):
        answers["is_commercial_use"] = False

    # Check entity nationality / foreign control
    if any(k in q for k in ["foreign company", "foreign entity", "multinational", "mnc", "foreign citizen", "nri", "non-resident indian", "foreign owned"]):
        answers["is_foreign_entity"] = True
    elif any(k in q for k in ["indian company", "indian citizen", "domestic entity", "local company", "ayush practitioner", "indian firm"]):
        answers["is_foreign_entity"] = False

    return answers


def get_next_abs_question(answers: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Returns the next pending question in the 3-step decision flow, or None if fully evaluated."""
    # Step 1: Sourced in India?
    if "is_sourced_from_india" not in answers or answers["is_sourced_from_india"] is None:
        return ABS_QUESTIONS[0]

    # If not sourced in India, flow terminates immediately (Section 3 & 7 do not apply)
    if not _is_yes(answers["is_sourced_from_india"]):
        return None

    # Step 2: Commercial use vs Research?
    if "is_commercial_use" not in answers or answers["is_commercial_use"] is None:
        return ABS_QUESTIONS[1]

    # Step 3: Foreign entity vs Indian domestic entity?
    if "is_foreign_entity" not in answers or answers["is_foreign_entity"] is None:
        return ABS_QUESTIONS[2]

    return None


def evaluate_abs_compliance(answers: Dict[str, Any], query: str = "") -> Dict[str, Any]:
    """Evaluates the structured ABS compliance obligations against the verified statutory text.

    Returns:
        Structured dictionary matching required prompt schema:
        {
          "requires_nba_approval": bool,
          "requires_sbb_intimation": bool,
          "applicable_provision": "<Section/Rule citation>",
          "next_steps": ["<plain-language step 1>", ...],
          "relevant_forms": ["<form name>"]
        }
    """
    state_name = detect_state_in_query(query)
    sbb_name = INDIAN_STATES_BOARDS.get(state_name.lower(), f"{state_name} State Biodiversity Board") if state_name else "concerned State Biodiversity Board (SBB)"

    is_india = _is_yes(answers.get("is_sourced_from_india"))
    is_comm = _is_yes(answers.get("is_commercial_use"))
    is_foreign = _is_yes(answers.get("is_foreign_entity"))

    # Outcome 1: Biological Resource NOT Sourced from India
    if is_india is False:
        return {
            "requires_nba_approval": False,
            "requires_sbb_intimation": False,
            "applicable_provision": "Section 3(1) & Section 7(1) read with Section 2(c), Biological Diversity Act, 2002 (as amended 2023)",
            "exact_statutory_text": (
                "Section 3(1) and Section 7(1) apply strictly to biological resources occurring in, or obtained or accessed from, India. "
                "Biological resources obtained entirely outside India are outside the territorial scope of the Indian Biological Diversity Act."
            ),
            "next_steps": [
                "Verify and retain country-of-origin documentation and legal access permits from the source nation.",
                "Ensure compliance with international ABS obligations (Nagoya Protocol / Convention on Biological Diversity) in the provider country.",
                "Verify Indian customs import clearance and DGFT / CITES documentation if the biological resource is imported into India.",
                "No NBA approval or State Biodiversity Board intimation is required under the Indian Biological Diversity Act.",
            ],
            "relevant_forms": [],
            "sbb_state": state_name,
            "summary": "Biological resource is obtained outside India; Indian BD Act ABS obligations do not apply.",
        }

    # If foreign entity status is not yet determined, default or provide conditional commercial domestic view
    # Outcome 2: Indian Domestic Entity + Commercial Utilization / Export
    if is_comm is True and is_foreign is False:
        sbb_intimation_form = f"Form I of {sbb_name} (Prior Intimation for Commercial Utilization)"
        return {
            "requires_nba_approval": False,
            "requires_sbb_intimation": True,
            "applicable_provision": "Section 7(1), Biological Diversity Act, 2002 (as substituted by Biological Diversity (Amendment) Act, 2023) read with State Biodiversity Rules",
            "exact_statutory_text": (
                "Section 7(1): 'No person, other than the person covered under sub-section (2) of section 3, shall access any biological resource "
                "and its associated knowledge for commercial utilisation, without giving prior intimation to the concerned State Biodiversity Board, "
                "but such access shall be subject to the provisions of clause (b) of section 23 and sub-section (2) of section 24.'"
            ),
            "next_steps": [
                f"Submit prior intimation to the {sbb_name} in the prescribed SBB Form I before commencing commercial access or export.",
                f"Declare the botanical name of the plant, specific parts used, and geographic harvesting location (Panchayat / Biodiversity Management Committee area) in {state_name or 'the State'}.",
                f"Enter into an Access and Benefit-Sharing (ABS) Agreement with the {sbb_name} determining the benefit-sharing percentage (typically 0.1% to 0.5% of ex-factory sale value under NBA ABS Regulations).",
                "Verify whether the plant is cultivated: under Section 7(1) & (2) as amended in 2023 and Rule 19 of BD (Amendment) Rules 2025, cultivated medicinal plants are EXEMPT from Section 7 if a Certificate of Origin is obtained in Form 12 from the local Biodiversity Management Committee (BMC).",
                "Note on IPR: If you later apply for a patent based on this formulation, you must register with the NBA before grant under Section 6(1A), and obtain NBA approval before commercialising the granted IPR under Section 6(1B).",
            ],
            "relevant_forms": [
                sbb_intimation_form,
                f"ABS Agreement with {sbb_name}",
                "Form 11A / Form 12 (Certificate of Origin from Biodiversity Management Committee for cultivated plants under 2025 BD Amendment Rules, if applicable)",
            ],
            "sbb_state": state_name,
            "summary": f"Prior intimation to {sbb_name} is mandatory under Section 7(1). Prior NBA approval under Section 3 is NOT required for Indian domestic entities.",
        }

    # Outcome 3: Foreign Entity / NRI / Foreign-Controlled Company + Commercial Utilization / Export
    if is_comm is True and is_foreign is True:
        return {
            "requires_nba_approval": True,
            "requires_sbb_intimation": False,
            "applicable_provision": "Section 3(1) read with Section 3(2), Biological Diversity Act, 2002 (as amended 2023) and Rule 13(1), Biological Diversity Rules, 2024",
            "exact_statutory_text": (
                "Section 3(1): 'No person referred to in sub-section (2) shall, without previous approval of the National Biodiversity Authority, "
                "obtain any biological resource occurring in India or knowledge associated thereto for research or for commercial utilisation or for bio-survey and bio-utilisation.' "
                "Rule 13(1), BD Rules 2024: 'Any person, referred to in sub-section (2) of section 3 of the Act, seeking approval of the Authority... for commercial utilisation shall make an application on the web portal of the Authority in Form 2.'"
            ),
            "next_steps": [
                "Submit an electronic application in Form 2 on the National Biodiversity Authority web portal (nbaindia.org) prior to accessing, procuring, or exporting the biological resource.",
                "Remit the prescribed statutory application fee via digital payment into the National Biodiversity Fund (Rule 13(3)).",
                "Execute a formal Access and Benefit-Sharing (ABS) Agreement on mutually agreed terms with the NBA authorized officer (Rule 13(5)).",
                "Await formal approval order from the NBA before exporting the formulation or processing commercial consignments.",
                "Section 7 SBB intimation is NOT required because Section 7(1) explicitly excludes persons covered under Section 3(2).",
            ],
            "relevant_forms": [
                "NBA Form 2 (Application for Access to Biological Resources and Associated Knowledge for Commercial Utilisation — Rule 13(1), BD Rules 2024)",
                "ABS Agreement with National Biodiversity Authority on Mutually Agreed Terms (Rule 13(5))",
            ],
            "sbb_state": state_name,
            "summary": "Mandatory prior approval from National Biodiversity Authority (NBA) in Form 2 under Section 3(1) is required. SBB intimation does not apply.",
        }

    # Outcome 4: Indian Domestic Entity + Research Only
    if is_comm is False and is_foreign is False:
        return {
            "requires_nba_approval": False,
            "requires_sbb_intimation": False,
            "applicable_provision": "Section 7(1) (Proviso & A Contrario), Biological Diversity Act, 2002 (as amended 2023)",
            "exact_statutory_text": (
                "Section 7(1) applies strictly to access for 'commercial utilisation'. Domestic Indian citizens and entities conducting "
                "non-commercial scientific research are not subject to Section 7 prior intimation, and Section 3 applies only to Section 3(2) entities."
            ),
            "next_steps": [
                "Non-commercial scientific research conducted domestically by Indian citizens or entities does not require prior NBA approval or SBB intimation.",
                "Maintain accurate laboratory records, research logs, and collection vouchers documenting domestic collection provenance.",
                "Crucial note: If research findings are subsequently commercialized, prior intimation to the SBB will become mandatory under Section 7.",
                "If filing a patent or intellectual property right based on the research, submit registration to the NBA in Form 7 before grant under Section 6(1A).",
            ],
            "relevant_forms": [
                "None for domestic scientific research (Form 7 required later if IPR/patent applied for)",
            ],
            "sbb_state": state_name,
            "summary": "Non-commercial scientific research by Indian entities requires neither NBA approval nor SBB intimation.",
        }

    # Outcome 5: Foreign Entity / NRI / Foreign-Controlled Company + Research Only
    if is_comm is False and is_foreign is True:
        return {
            "requires_nba_approval": True,
            "requires_sbb_intimation": False,
            "applicable_provision": "Section 3(1), Section 3(2) & Section 5(1), Biological Diversity Act, 2002 (as amended 2023) read with Rule 13(1), BD Rules, 2024",
            "exact_statutory_text": (
                "Section 3(1): 'No person referred to in sub-section (2) shall, without previous approval of the National Biodiversity Authority, "
                "obtain any biological resource occurring in India or knowledge associated thereto for research...'"
                "Rule 13(1), BD Rules 2024: 'Any person, referred to in sub-section (2) of section 3 of the Act, seeking approval of the Authority for access... for research or for bio-survey and bio-utilisation shall make an application on the web portal of the Authority in Form 1.'"
            ),
            "next_steps": [
                "Submit an application in Form 1 on the NBA web portal (nbaindia.org) for access to Indian biological resources for research or bio-survey.",
                "Pay the prescribed statutory application fee to the National Biodiversity Fund.",
                "Execute the research access agreement with the NBA.",
                "Exemption check: Under Section 5(1), collaborative research projects between Indian and foreign institutions conforming to Central Government approval guidelines are exempt from Section 3.",
                "Results of research cannot be transferred to third parties without prior NBA approval in Form 3 under Section 4 and Rule 15.",
            ],
            "relevant_forms": [
                "NBA Form 1 (Application for Access for Research / Bio-survey — Rule 13(1), BD Rules 2024)",
                "Section 5 Central Government Collaborative Research Clearance (if claiming exemption)",
            ],
            "sbb_state": state_name,
            "summary": "Prior approval from NBA in Form 1 is required for foreign entities conducting research on Indian biological resources.",
        }

    # Default fallback for partial answers: provide comparison between Domestic vs Foreign commercial utilization
    return {
        "requires_nba_approval": False,
        "requires_sbb_intimation": True,
        "applicable_provision": "Section 7(1) (Domestic) vs Section 3(1) (Foreign), Biological Diversity Act, 2002 (as amended 2023)",
        "exact_statutory_text": (
            "Section 7(1) mandates prior intimation to the State Biodiversity Board for Indian domestic entities commercializing Indian biological resources. "
            "Section 3(1) mandates prior approval from the National Biodiversity Authority for foreign entities / NRIs / foreigner-controlled corporations."
        ),
        "next_steps": [
            f"If Indian domestic entity: Submit prior intimation in SBB Form I to {sbb_name} before commercial export.",
            "If foreign entity, NRI, or foreign-controlled company: Apply for prior approval from the National Biodiversity Authority (NBA) in Form 2.",
        ],
        "relevant_forms": [
            f"SBB Form I ({sbb_name})",
            "NBA Form 2 (Commercial Access)",
        ],
        "sbb_state": state_name,
        "summary": "Compliance depends on applicant entity nationality. Indian domestic entities require SBB intimation; Section 3(2) foreign entities require NBA approval.",
    }


def process_abs_decision_flow(
    query: str,
    user_answers: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Coordinates trigger detection, answer extraction, decision flow question state, and compliance calculation.

    Returns payload structure for API responses and frontend panel.
    """
    triggered = detect_abs_trigger(query)
    if not triggered and not user_answers:
        return {
            "triggered": False,
            "status": "not_triggered",
            "answers": {},
            "next_question": None,
            "result": None,
        }

    # 1. Merge extracted answers with user answers (user answers take precedence)
    extracted = extract_abs_initial_answers(query)
    merged_answers: Dict[str, Any] = dict(extracted)
    if user_answers:
        for k, v in user_answers.items():
            if v is not None:
                merged_answers[k] = v

    # 2. Check if there is a pending question
    next_q = get_next_abs_question(merged_answers)

    # 3. Evaluate compliance based on current merged answers
    # Even if next_q is present, we compute the provisional or domestic-standard result so the panel has actionable guidance
    result = evaluate_abs_compliance(merged_answers, query=query)

    is_complete = next_q is None

    return {
        "triggered": True,
        "status": "completed" if is_complete else "needs_input",
        "answers": merged_answers,
        "next_question": next_q,
        "result": result,
    }
