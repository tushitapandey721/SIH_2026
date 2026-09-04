"""Test new chunker implementation on Patents Act and all 4 international treaties."""

import re
import sys
from pathlib import Path
sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

from app.ingestion.extract import extract_native, clean_text


def test_chunker():
    # 1. Test Patents Act Section 2 chunking
    p_path = Path("data/corpus/national/Patents Act, 1970.pdf")
    text = clean_text(extract_native(p_path))
    
    # Check Section 2 extraction
    m = re.search(r"(?:2\.\s+Definitions|Section\s+2\b)(.*?)(?:3\.\s+What\s+are\s+not|CHAPTER\s+II)", text, re.DOTALL | re.IGNORECASE)
    sec2_text = m.group(0)
    
    subclause_pattern = re.compile(r'(?m)(?:^|\n\s*)(\([a-z0-9]{1,3}\))\s*(?:[\"“]([^\"”\n]+)[\"”])?', re.IGNORECASE)
    matches = list(subclause_pattern.finditer(sec2_text))
    print(f"Patents Act Section 2: Found {len(matches)} subclause definitions:")
    key_clauses = {}
    for idx, match in enumerate(matches):
        c_letter = match.group(1).strip("()")
        term = match.group(2)
        start_p = match.start()
        end_p = matches[idx + 1].start() if idx + 1 < len(matches) else len(sec2_text)
        c_text = sec2_text[start_p:end_p].strip()
        sec_id = f"Section 2(1)({c_letter})" + (f' "{term}"' if term else "")
        if c_letter in ["j", "ja", "l", "ta", "ac", "w", "aba"]:
            key_clauses[c_letter] = (sec_id, c_text)
            print(f"  • {sec_id}")
            print(f"    Text: {c_text[:120]}...\n")

    # 2. Test Treaty Article extraction
    treaties = [
        ("Nagoya Protocol.pdf", "Nagoya Protocol"),
        ("trips_agreement.pdf", "TRIPS Agreement"),
        ("Convention on Biological Diversity (CBD).pdf", "CBD"),
        ("PCT (Patent Cooperation Treaty).pdf", "PCT"),
    ]
    
    art_pattern = re.compile(
        r"(?im)(?:^|\n\s*)(?:ARTICLE|Article|Art\.)\s*\n*\s*(\d+[A-Za-z]?)(?:[\.\:\s—–\-]*\n*\s*([A-Z][a-zA-Z0-9\s,\-–\(\)\/]{2,80}))?"
    )

    for filename, doc_name in treaties:
        for p in Path("data/corpus/international").rglob(f"*{filename}*"):
            raw = clean_text(extract_native(p))
            art_matches = list(art_pattern.finditer(raw))
            print(f"\n==================================================")
            print(f"{doc_name}: Found {len(art_matches)} Articles")
            print(f"Sample Articles:")
            for m in art_matches[:6]:
                num = m.group(1)
                title = m.group(2) or ""
                # Clean title
                clean_t = re.sub(r"\s+", " ", title).strip().rstrip(".:—– ")
                print(f"  • Article {num}" + (f": {clean_t}" if clean_t else ""))

test_chunker()
