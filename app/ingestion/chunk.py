"""Legal text chunking engine with statutory section/article regex splitting, lettered sub-clause extraction, TOC filtering, and recursive fallback."""

import re
import logging
from typing import List, Dict, Any, Optional
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

# Primary regex matching statutory Sections, Rules, Regulations, and Treaty Articles
ARTICLE_PATTERN = re.compile(
    r"(?im)^(?:\s*(?:ARTICLE|Article|Art\.)\s+(\d+[A-Za-z]?)(?:[\.\:\s—–\-]*\n*\s*([A-Z][^\n]{2,80}))?)"
)

SECTION_RULE_PATTERN = re.compile(
    r"(?m)(?:^|\n\s*)("
    r"(?:Section|Sec\.)\s+\d+[A-Za-z]?(?:[\.\:\—–\-]+|\s+[A-Z][^\n]{2,80})"
    r"|(?:Rule|Regulation|Reg\.)\s+\d+[A-Za-z]?(?:[\.\:\—–\-]+|\s+[A-Z][^\n]{2,80}|\b)"
    r"|\b\d+[A-Za-z]?\.\s+[A-Z][^\n]{2,80}"
    r")"
)

# Sub-clause regex capturing (a), (j), (ja), (l), (ta) at start of lines with optional definition term
SUBCLAUSE_PATTERN = re.compile(
    r'(?m)(?:^|\n\s*)(\([a-z0-9]{1,3}\))\s*(?:[\"“]([^\"”\n]+)[\"”])?',
    re.IGNORECASE,
)

# Fallback recursive text splitter (chunk_size=1200, overlap=150)
DEFAULT_SPLITTER = RecursiveCharacterTextSplitter(
    chunk_size=1400,
    chunk_overlap=150,
    separators=["\n\n", "\n", "; ", ". ", " ", ""],
)

# CBD Article Title Restoration Map
CBD_ARTICLE_MAP = {
    "Objectives": "1",
    "Use of Terms": "2",
    "Principle": "3",
    "Jurisdictional Scope": "4",
    "Cooperation": "5",
    "General Measures for Conservation": "6",
    "Identification and Monitoring": "7",
    "In-situ Conservation": "8",
    "Ex-situ Conservation": "9",
    "Sustainable Use of Components": "10",
    "Incentive Measures": "11",
    "Research and Training": "12",
    "Public Education and Awareness": "13",
    "Impact Assessment and Minimizing": "14",
    "Access to Genetic Resources": "15",
    "Access to and Transfer of Technology": "16",
    "Exchange of Information": "17",
    "Technical and Scientific Cooperation": "18",
    "Handling of Biotechnology": "19",
    "Financial Resources": "20",
    "Financial Mechanism": "21",
    "Relationship with Other International": "22",
    "Conference of the Parties": "23",
    "Secretariat": "24",
    "Subsidiary Body": "25",
    "Reports": "26",
    "Settlement of Disputes": "27",
    "Adoption of Protocols": "28",
    "Amendment of the Convention": "29",
    "Adoption and Amendment of Annexes": "30",
    "Right to Vote": "31",
    "Relationship between this Convention": "32",
    "Signature": "33",
    "Ratification, Acceptance": "34",
    "Accession": "35",
    "Entry into Force": "36",
    "Reservations": "37",
    "Withdrawals": "38",
    "Financial Interim Arrangements": "39",
    "Secretariat Interim Arrangements": "40",
    "Depositary": "41",
    "Authentic Texts": "42",
}

# Nagoya Protocol Article Title Restoration Map
NAGOYA_ARTICLE_MAP = {
    "OBJECTIVE": "1",
    "USE OF TERMS": "2",
    "SCOPE": "3",
    "RELATIONSHIP WITH INTERNATIONAL": "4",
    "FAIR AND EQUITABLE BENEFIT-SHARING": "5",
    "ACCESS TO GENETIC RESOURCES": "6",
    "ACCESS TO TRADITIONAL KNOWLEDGE": "7",
    "SPECIAL CONSIDERATIONS": "8",
    "CONTRIBUTION TO CONSERVATION": "9",
    "GLOBAL MULTILATERAL BENEFIT-SHARING": "10",
    "TRANSBOUNDARY COOPERATION": "11",
    "TRADITIONAL KNOWLEDGE ASSOCIATED": "12",
    "NATIONAL FOCAL POINTS": "13",
    "THE ACCESS AND BENEFIT-SHARING CLEARING-HOUSE": "14",
    "COMPLIANCE WITH DOMESTIC LEGISLATION OR REGULATORY REQUIREMENTS ON ACCESS AND BENEFIT-SHARING FOR TRADITIONAL": "16",
    "COMPLIANCE WITH DOMESTIC LEGISLATION": "15",
    "MONITORING THE UTILIZATION": "17",
    "COMPLIANCE WITH MUTUALLY AGREED TERMS": "18",
    "MODEL CONTRACTUAL CLAUSES": "19",
    "CODES OF CONDUCT": "20",
    "AWARENESS-RAISING": "21",
    "CAPACITY": "22",
    "TECHNOLOGY TRANSFER": "23",
    "NON-PARTIES": "24",
    "FINANCIAL MECHANISM": "25",
    "CONFERENCE OF THE PARTIES": "26",
    "SUBSIDIARY BODIES": "27",
    "SECRETARIAT": "28",
    "MONITORING AND REPORTING": "29",
    "PROCEDURES AND MECHANISMS": "30",
    "ASSESSMENT AND REVIEW": "31",
    "SIGNATURE": "32",
    "ENTRY INTO FORCE": "33",
    "RESERVATIONS": "34",
    "WITHDRAWAL": "35",
    "AUTHENTIC TEXTS": "36",
}


def clean_legal_text(raw_text: str) -> str:
    """Cleans footnote markers, marginal annotations, and editorial brackets that disrupt legal regex parsing."""
    if not raw_text:
        return ""
    text = raw_text
    # Remove footnote brackets like 1[PART XVII ...], 2[Labelling...], [1], [2], 3[with the botanical names...
    text = re.sub(r'\b\d+\[', '', text)
    text = re.sub(r'(?m)^\s*\d+\[', '', text)
    text = re.sub(r'\[\s*\d+\s*\]', '', text)
    # Remove footnote lines at bottom of pages: e.g. "1. Subs. by G.S.R...", "2. Ins. by..."
    text = re.sub(r'(?m)^\s*\d+\.\s+(?:Subs\.|Ins\.|Omitted|Added)\s+by\s+.*$', '', text)
    return text


def filter_table_of_contents(text: str) -> str:
    """Strips preliminary table-of-contents / arrangement of sections from domestic Acts."""
    # Look for start of substantive provisions (e.g. CHAPTER I / PRELIMINARY / Section 1. Short title)
    m_body = re.search(r'(?im)(?:^|\n\s*)(?:CHAPTER\s+I\b|PRELIMINARY\b|(?:Section\s+1|1)\.\s+Short\s+title)', text)
    if m_body and m_body.start() > 300:
        # Check if text before m_body has TOC patterns (e.g. ARRANGEMENT OF SECTIONS or list of sections)
        header_text = text[:m_body.start()]
        if "ARRANGEMENT OF SECTIONS" in header_text.upper() or "ARRANGEMENT OF CLAUSES" in header_text.upper() or "SECTIONS" in header_text.upper():
            return text[m_body.start():]
    return text


def extract_section_markers(text: str, is_treaty: bool = False, chunk_strategy: str = "section") -> List[Dict[str, Any]]:
    """Identifies statutory section, rule, regulation, and article markers in legal text."""
    if not text or not text.strip():
        return []

    cleaned = clean_legal_text(text)
    if not is_treaty:
        cleaned = filter_table_of_contents(cleaned)

    sections: List[Dict[str, Any]] = []

    # If document is an international treaty (or contains prominent Article markers), prioritize Article splitting
    if is_treaty:
        prep_text = cleaned

        if "Table of Contents" in prep_text[:3000] or "TABLE OF CONTENTS" in prep_text[:3000]:
            m_body = re.search(r"(?im)^(?:\s*ARTICLE\s+1\b|\s*Article\s+1\b)", prep_text[400:])
            if m_body:
                prep_text = prep_text[400 + m_body.start():]

        is_nagoya = "nagoya" in prep_text[:1000].lower()
        is_cbd = ("convention on biological diversity" in prep_text[:1000].lower() or "biological diversity" in prep_text[:1000].lower()) and not is_nagoya

        if is_nagoya:
            for title_key, num in NAGOYA_ARTICLE_MAP.items():
                prep_text = re.sub(
                    rf"(?im)\n\s*Article\s*\n+\s*({re.escape(title_key)}[^\n]*)",
                    rf"\nArticle {num}. \1",
                    prep_text,
                )
        elif is_cbd:
            for title_key, num in CBD_ARTICLE_MAP.items():
                prep_text = re.sub(
                    rf"(?im)\n\s*Article\s*\n+\s*({re.escape(title_key)}[^\n]*)",
                    rf"\nArticle {num}. \1",
                    prep_text,
                )

        art_matches = list(ARTICLE_PATTERN.finditer(prep_text))
        if art_matches:
            if art_matches[0].start() > 50:
                preamble = prep_text[:art_matches[0].start()].strip()
                if len(preamble) >= 50:
                    sections.append({
                        "section_id": "Preamble / Preliminary",
                        "text": preamble,
                    })

            for idx, match in enumerate(art_matches):
                art_num = match.group(1)
                full_marker = match.group(0).strip()
                m_title = re.search(r"(?:ARTICLE|Article|Art\.)\s+\d+[A-Za-z]?[\.\:\—–\-\s\n]+([A-Z][^\n]{2,80})", full_marker)
                art_title = m_title.group(1) if m_title else ""
                if not art_title:
                    match_end = match.end()
                    next_chunk = prep_text[match_end:match_end+120].strip()
                    m_next = re.match(r"^([A-Z\s,\-–\(\)\/]{2,80})", next_chunk)
                    if m_next:
                        art_title = m_next.group(1).strip()

                clean_title = re.sub(r"\s+", " ", art_title).strip().rstrip(".:—– ")
                if clean_title and len(clean_title) > 60:
                    clean_title = clean_title[:57] + "..."

                section_id = f"Article {art_num}" + (f": {clean_title}" if clean_title else "")
                start_p = match.start()
                end_p = art_matches[idx + 1].start() if idx + 1 < len(art_matches) else len(prep_text)
                sec_text = prep_text[start_p:end_p].strip()

                sections.append({
                    "section_id": section_id,
                    "text": sec_text,
                })
            return sections

    # Standard Section / Rule extraction for domestic statutes
    matches = list(SECTION_RULE_PATTERN.finditer(cleaned))
    if not matches:
        return []

    # Check for preamble text before the first section marker
    if matches[0].start() > 50:
        preamble_text = cleaned[:matches[0].start()].strip()
        if len(preamble_text) >= 50:
            sections.append({
                "section_id": "Preamble / Preliminary",
                "text": preamble_text,
            })

    default_type = "Rule" if chunk_strategy.lower() in ("rule", "regulation") else "Section"

    for idx, match in enumerate(matches):
        marker_raw = match.group(1).strip().rstrip(".:—– ")
        marker_clean = re.sub(r"[\[\]]", "", marker_raw).strip()

        # Extract rule/section number and clean title before em-dash or sub-rules
        m_num_title = re.match(r"^((?:Section|Sec\.|Rule|Regulation|Reg\.)\s+\d+[A-Za-z]?|\d+[A-Za-z]?)(?:[\.\:\—–\-\s]+([^—–\(\n]+))?", marker_clean)
        if m_num_title:
            prefix_or_num = m_num_title.group(1).strip()
            raw_title = (m_num_title.group(2) or "").strip().rstrip(".:—– ")
            if re.match(r"^\d+[A-Za-z]?$", prefix_or_num):
                num_val = int(re.match(r"^(\d+)", prefix_or_num).group(1))
                if chunk_strategy.lower() in ("rule", "regulation") or (num_val >= 100 and "Rules" in text[:400]):
                    section_id = f"Rule {prefix_or_num}" + (f" — {raw_title}" if raw_title else "")
                else:
                    section_id = f"{default_type} {prefix_or_num}" + (f" — {raw_title}" if raw_title else "")
            else:
                p_clean = re.sub(r"^(Sec\.|Sec\b)", "Section", prefix_or_num, flags=re.IGNORECASE)
                p_clean = re.sub(r"^(Reg\.|Reg\b)", "Regulation", p_clean, flags=re.IGNORECASE)
                section_id = f"{p_clean}" + (f" — {raw_title}" if raw_title else "")
        else:
            section_id = marker_clean

        section_id = re.sub(r"\s+", " ", section_id).strip()
        if len(section_id) > 75:
            section_id = section_id[:72] + "..."

        start_pos = match.start()
        end_pos = matches[idx + 1].start() if idx + 1 < len(matches) else len(cleaned)
        section_text = cleaned[start_pos:end_pos].strip()

        # Discard TOC stub matches (< 80 chars)
        if len(section_text) < 80 and idx + 1 < len(matches):
            continue

        sections.append({
            "section_id": section_id,
            "text": section_text,
        })

    return sections


def chunk_document(
    text: str,
    chunk_strategy: str = "section",
    max_section_length: int = 5000,
    min_fragment_length: int = 60,
) -> List[Dict[str, str]]:
    """Splits legal text on statutory markers with sub-clause definition extraction and recursive fallback."""
    if not text or not text.strip():
        return []

    is_treaty = chunk_strategy.lower() in {"article", "treaty"} or bool(re.search(r"(?im)^\s*(?:ARTICLE|Article)\s+\d+", text))
    section_pieces = extract_section_markers(text, is_treaty=is_treaty, chunk_strategy=chunk_strategy)
    final_chunks: List[Dict[str, str]] = []

    if section_pieces:
        for item in section_pieces:
            sec_id = item["section_id"]
            sec_text = item["text"]

            # Sub-clause pass for definitional or exclusion sections (e.g. Section 2, Section 3)
            sub_matches = list(SUBCLAUSE_PATTERN.finditer(sec_text))
            if len(sub_matches) >= 3 and ("Section 2" in sec_id or "Section 3" in sec_id or "Rule 2" in sec_id or "Rule 3" in sec_id or "Definitions" in sec_id or "NOT PATENTABLE" in sec_id):
                m_base = re.search(r"\b(Section|Rule|Article|Regulation)\s+\d+[A-Za-z]?", sec_id, re.IGNORECASE)
                parent_base = m_base.group(0) if m_base else sec_id

                intro_text = sec_text[:sub_matches[0].start()].strip()
                if len(intro_text) >= min_fragment_length:
                    final_chunks.append({
                        "section_id": f"{parent_base} (Preamble/Definitions)",
                        "text": intro_text,
                    })

                is_sec2 = "2" in parent_base or "Definitions" in sec_id

                for idx, match in enumerate(sub_matches):
                    clause_letter = match.group(1).strip("()")
                    term = match.group(2)
                    start_p = match.start()
                    end_p = sub_matches[idx + 1].start() if idx + 1 < len(sub_matches) else len(sec_text)
                    clause_text = sec_text[start_p:end_p].strip()

                    # Skip empty/purely numbered headers
                    if not clause_text or len(clause_text) < min_fragment_length:
                        continue

                    if is_sec2:
                        clause_id = f"{parent_base}(1)({clause_letter})" + (f' "{term}"' if term else "")
                        header_prefix = f"{sec_id}\n(1) In this Act, unless the context otherwise requires,—\n"
                    elif "not patentable" in sec_id.lower() or "not patentable" in sec_text.lower() or ("section 3" in sec_id.lower() and "invention" in sec_text.lower()):
                        clause_id = f"{parent_base}({clause_letter})"
                        header_prefix = f"{sec_id}\nThe following are not inventions within the meaning of this Act,—\n"
                    else:
                        clause_id = f"{parent_base}({clause_letter})"
                        header_prefix = f"{sec_id}\n"

                    full_clause_text = f"{header_prefix}{clause_text}".strip()

                    if len(full_clause_text) > max_section_length:
                        sub_splits = DEFAULT_SPLITTER.split_text(full_clause_text)
                        for p_idx, s_txt in enumerate(sub_splits, start=1):
                            final_chunks.append({
                                "section_id": f"{clause_id} (Part {p_idx})",
                                "text": s_txt.strip(),
                            })
                    else:
                        final_chunks.append({
                            "section_id": clause_id,
                            "text": full_clause_text,
                        })
                continue

            # Standard Section/Article chunking
            if len(sec_text) > max_section_length:
                sub_splits = DEFAULT_SPLITTER.split_text(sec_text)
                for part_idx, sub_text in enumerate(sub_splits, start=1):
                    if len(sub_text.strip()) >= min_fragment_length:
                        sub_id = f"{sec_id} (Part {part_idx})" if len(sub_splits) > 1 else sec_id
                        p_text = f"{sec_id}\n{sub_text.strip()}" if not sub_text.strip().startswith(sec_id) else sub_text.strip()
                        final_chunks.append({
                            "section_id": sub_id,
                            "text": p_text,
                        })
            else:
                if len(sec_text.strip()) >= min_fragment_length:
                    p_text = f"{sec_id}\n{sec_text.strip()}" if not sec_text.strip().startswith(sec_id) else sec_text.strip()
                    final_chunks.append({
                        "section_id": sec_id,
                        "text": p_text,
                    })
    else:
        splits = DEFAULT_SPLITTER.split_text(text)
        for part_idx, chunk_text in enumerate(splits, start=1):
            if len(chunk_text.strip()) >= min_fragment_length:
                final_chunks.append({
                    "section_id": f"General (Part {part_idx})",
                    "text": chunk_text.strip(),
                })

    return final_chunks
